import argparse
import os
import pathlib
import traceback
from typing import Callable

import yaml
from beets import config, ui
from beets.dbcore.query import MatchQuery
from beets.library import Item
from beets.plugins import BeetsPlugin
from beets.util import normpath
from plexapi import exceptions
from plexapi.server import PlexServer
from slugify import slugify


class GdPlaylists(BeetsPlugin):
    def __init__(self):
        super(GdPlaylists, self).__init__()

        self.config_dir = config.config_dir()

        config["plex"].add(
            {
                "host": "localhost",
                "port": "",
                "token": "",
                "library_name": "Music",
                "secure": False,
                "ignore_cert_errors": False,
            }
        )

        default_playlist_dir = os.path.join(config["directory"].get(), ".playlists")
        config["gdplex"].add({"playlist_dir": default_playlist_dir})
        config["gdplex"].add({"remote_dir": default_playlist_dir})

        config["plex"]["token"].redact = True
        protocol = "https" if config["plex"]["secure"].get() else "http"

        baseurl = f"{protocol}://" + config["plex"]["host"].get()

        self.plex_url = baseurl
        self.plex = None
        self.music = None


    def setup(self):
        if self.plex is not None:
            return

        try:
            self._log.debug("Attempting to connect to {}", self.plex_url)
            self.plex = PlexServer(self.plex_url, config["plex"]["token"].get())
            self._log.debug("Connection established")
        except exceptions.Unauthorized:
            raise ui.UserError("Plex authorization failed")

        try:
            self.music = self.plex.library.section(config["plex"]["library_name"].get())
        except exceptions.NotFound:
            raise ui.UserError(f"{config['plex']['library_name']} library not found")


    def config_playlist_dir(self) -> str:
        key = "playlist_dir"
        return normpath(self.config[key].get(str)).decode("utf-8")

    def config_remote_dir(self) -> str:
        key = "remote_dir"
        return normpath(self.config[key].get(str)).decode("utf-8")

    def _create_playlist(self, lib, title, tracks, playlist_dir, remote_dir):
        with lib.transaction():
            playlist_tracks = []
            for t in tracks:
                query = MatchQuery("mb_trackid", t["mbid"], fast=True)
                found = lib.items(query)
                if found:
                    playlist_tracks.append(found[0])

        # Create m3u playlist
        if len(playlist_tracks) == 0:
            self._log.debug("No tracks found for {}", title)
            return

        item_path: Callable[[Item], str] = lambda item: item.path.decode("utf-8")
        paths = [item_path(item) for item in playlist_tracks]

        filename = slugify(title) + ".m3u"
        full_path = os.path.join(playlist_dir, filename)

        self._log.debug("Opening playlist file for writing: {}", full_path)
        with open(full_path, "w") as file:
            write_str = "\n".join(paths)
            file.write(write_str)

        self._log.debug(
            "Creating plex playlist from {}", os.path.join(remote_dir, filename)
        )
        try:
            self.plex.createPlaylist(
                title,
                section=self.music,
                m3ufilepath=os.path.join(remote_dir, filename),
            )
        except Exception as e:
            traceback.print_exc()
            self._log.error("Error creating playlist: {}", e)

    def sync(self, lib, playlist_dir, remote_dir):
        self.setup()
        if playlist_dir is None:
            playlist_dir = self.config_playlist_dir()

        if remote_dir is None:
            remote_dir = self.config_remote_dir()

        base = pathlib.Path(
            os.path.join(pathlib.Path(__file__).parent.absolute(), "playlists")
        )
        for item in base.iterdir():
            if item.is_dir():
                continue

            with open(str(item), "r") as _f:
                data = yaml.safe_load(_f)
                self._create_playlist(
                    lib, data["title"], data["tracks"], playlist_dir, remote_dir
                )

    def commands(self) -> list[ui.Subcommand]:
        cmd = SyncCommand(self)

        return [cmd]


class SyncCommand(ui.Subcommand):
    name = "gdplex"
    aliases = ()
    help = "Sync Grateful Dead live releases as plex playlists"

    def __init__(self, plugin: GdPlaylists):
        self.plugin = plugin

        parser = argparse.ArgumentParser()
        parser.set_defaults(func=self.sync)

        subparsers = parser.add_subparsers(
            prog=parser.prog + " gdplaylists", dest="command", required=False
        )

        sync_parser = subparsers.add_parser("sync")
        sync_parser.set_defaults(func=self.sync)
        sync_parser.add_argument(
            "--playlist-dir",
            dest="playlist_dir",
            metavar="PATH",
            help="local directory to write files to",
        )
        sync_parser.add_argument(
            "--remote-playlist-dir",
            dest="remote_dir",
            metavar="PATH",
            help="where plex will see the playlist_dir",
        )

        super(SyncCommand, self).__init__(
            self.name, parser, self.help, aliases=self.aliases
        )

    def sync(self, lib, opts):
        o = vars(opts)
        self.plugin.sync(lib, o.get("playlist_dir"), o.get("remote_dir"))

    def func(self, lib, opts, _):
        opts.func(lib, opts)

    def parse_args(self, args):
        return self.parser.parse_args(args), []

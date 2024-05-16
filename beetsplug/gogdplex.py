import os
import pathlib

import yaml
from beets import config, ui
from beets.dbcore.query import MatchQuery
from beets.plugins import BeetsPlugin
from plexapi import exceptions
from plexapi.server import PlexServer


class GogdPlug(BeetsPlugin):
    def __init__(self):
        super().__init__()

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
        config["plex"]["token"].redact = True
        protocol = "https" if config["plex"]["secure"].get() else "http"

        baseurl = f"{protocol}://" + config["plex"]["host"].get()
        try:
            print(f"Attempting to connect to {baseurl}")
            self.plex = PlexServer(baseurl, config["plex"]["token"].get())
        except exceptions.Unauthorized:
            raise ui.UserError("Plex authorization failed")
        try:
            self.music = self.plex.library.section(config["plex"]["library_name"].get())
        except exceptions.NotFound:
            raise ui.UserError(
                f"{config['plex']['library_name']} \
                library not found"
            )

    def search_plex_track(self, item):
        """Fetch the Plex track key."""
        tracks = self.music.searchTracks(
            **{"album.title": item.album, "track.title": item.title}
        )
        if len(tracks) == 1:
            return tracks[0]
        elif len(tracks) > 1:
            for track in tracks:
                if track.parentTitle == item.album and track.title == item.title:
                    return track
        else:
            self._log.info("Track {} not found in Plex library", item)
            return None

    def _create_playlist(self, lib, title, tracks):
        with lib.transaction():
            playlist_tracks = []
            for t in tracks:
                query = MatchQuery("mb_trackid", t["mbid"], fast=True)
                found = lib.items(query)
                if found:
                    playlist_tracks.append(found[0])

        plex_tracks = list(
            filter(
                lambda x: x is not None,
                [self.search_plex_track(t) for t in playlist_tracks],
            )
        )
        try:
            playlist = self.plex.playlist(title)
        except exceptions.NotFound:
            playlist = None

        if playlist is None:
            self.plex.createPlaylist(title, items=list(plex_tracks))
        else:
            current_items = playlist.items()
            playlist.removeItems(current_items)
            playlist.addItems(plex_tracks)

    def commands(self):
        sync_command = ui.Subcommand(
            "gogdsync", help="Sync Grateful Dead releases as plex playlist"
        )

        def sync_playlists(lib, opts, args):
            base = pathlib.Path(
                os.path.join(pathlib.Path(__file__).parent.absolute(), "playlists")
            )
            for item in base.iterdir():
                if item.is_dir():
                    continue

                with open(str(item), "r") as _f:
                    data = yaml.safe_load(_f)
                    self._create_playlist(lib, data["title"], data["tracks"])

        sync_command.func = sync_playlists

        return [sync_command]

# beets-gogd-plex

A plugin for [beets](https://github.com/beetbox/beets) to create playlists for live Grateful Dead releases in your library.

It came about because I wanted to be able to listen to individual shows with their tracks in the right order, as opposed 
to the disc order which might have been changed to fit more onto the discs.


# Features

* Creates Plex playlists from releases it finds in your collection
* Updates the same playlists if you add more releases to your library


It does this by creating m3u playlist files for each show that it knows about
and can find tracks for you in your library. This all done by Musicbrainz track IDs, so your 
library will need to be properly tagged.

The m3u file is copied to where your Plex server can read it, and then Plex is instructed
to create a playlist.


# Installation

```sh
python3 -m pip install beets-gdplaylists

```


# Configuration

Enabled the plugin:

```yaml
plugins:
    - gdplaylists
```

Ensure your plex connection is configured:

```yaml
plex:
    host: localhost
    secure: false
    token: &lt;your token here&gt;
    library_name: "Music"
```

By default, the m3u files will be placed in a directory called `.playlists` in the root
of your library (`directory` in your config file). If you need to change that, you can 
reconfigure the plugin:

```yaml
gdplex:
    playlist_dir: "/Volumes/music/.playlists/"
    # remote_dir: "/music/.playlists/"
```

If, for some reason, this means the directory that Plex sees is different, you can configure
that with the `remote_dir` field. If your beets and plex servers see the same files at 
the same paths, you won't need that at all.


# Usage

```sh
beet gdplex

```

By default it's very quiet, you can use `beet -vv gdplex` to see what it's doing.

import musicbrainzngs
import sys
from yaml import dump

musicbrainzngs.set_useragent("beets-gogdplex", "0.1", "rhendry@gmail.com")

def download_tracks(mbid):
    try:
        print(f"Getting release data for {mbid}")
        # Get release information
        release_info = musicbrainzngs.get_release_by_id(mbid, 
                                                        includes=[
                                                            "recordings", 
                                                            "recording-rels", 
                                                            "recording-level-rels", 
                                                            "work-rels",
                                                            "work-level-rels",
                                                        ])
        # print(json.dumps(release_info, indent=4))
    
        playlist = {}
        playlist["title"] = release_info.get("release").get("title")
        playlist["tracks"] = []

        last_date = None
        for m in release_info.get('release').get('medium-list'):
            tracks = m.get('track-list')
            for track in tracks:
                recording = track.get('recording')
                work_relations = recording.get("work-relation-list", [])
                performances = list(filter(lambda x: x.get("type") == "performance", work_relations))
                d = "unknown"
                if len(performances) > 0:
                    d = performances[0].get("begin")
                    if d is not None:
                        last_date = d
                else:
                    if last_date is not None:
                        d = last_date
                print(f"Track {track.get('number')}: {recording.get('title')} ({d})")

                playlist["tracks"].append({
                    "title": recording.get("title"),
                    "date": d,
                    "mbid": recording.get("id"),
                    "from": playlist.get("title"),
                    "from_mbid": release_info.get("release").get("id")
                })

        with open("playlist.yml", "w") as file:
            dump(playlist, file, sort_keys=False)
        # print(dump(playlist, Dumper=Dumper, sort_keys=False)) 

    except musicbrainzngs.ResponseError as e:
        print("MusicBrainz API error:", e)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <musicbrainz release id>")
    else:
        mbid = sys.argv[1]
        download_tracks(mbid)


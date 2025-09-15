using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.Serialization;

namespace Reactional.Core
{
    internal class AssetHelper : MonoBehaviour
    {
        List<string> themes = new List<string>();
        List<string> tracks = new List<string>();

        // TODO: Make async?
        public static int AddTrackFromPath(Engine engine, string path)
        {
            if (Application.platform == RuntimePlatform.Android)
            {
                UnityEngine.Networking.UnityWebRequest www = UnityEngine.Networking.UnityWebRequest.Get(path);
                www.SendWebRequest();
                while (!www.isDone)
                {
                }
                return CheckTrackID(engine.AddTrackFromBytes(www.downloadHandler.data));
            }
            else
                return CheckTrackID(engine.AddTrackFromPath(path));
        }

        static Dictionary<string, object> ReadTrackMetadataFromPath(string path, string trackpath, Engine engine = null)
        {
            var trackPath = path + "/" + trackpath;

            string jsonText;
            if (Application.platform == RuntimePlatform.Android)
            {
                UnityEngine.Networking.UnityWebRequest www = UnityEngine.Networking.UnityWebRequest.Get(trackPath);
                www.SendWebRequest();
                while (!www.isDone)
                {
                }
                jsonText = Reactional.Core.Engine.GetTrackMetadata(www.downloadHandler.data);
            }
            else
            {
                byte[] data = File.ReadAllBytes(trackPath);
                jsonText = Reactional.Core.Engine.GetTrackMetadata(data);
            }

            Dictionary<string, object> dict = new Dictionary<string, object>();
            if (!string.IsNullOrEmpty(jsonText))
            {
                var meta = MiniJSON.Json.Deserialize(jsonText) as Dictionary<string, object>;
                
                dict.Add("name",       meta.ContainsKey("title")      ? meta["title"]?.ToString()      : " ");
                dict.Add("artists",    meta.ContainsKey("artists")    ? meta["artists"]?.ToString()    : " ");
                dict.Add("title",      meta.ContainsKey("title")      ? meta["title"]?.ToString()      : " ");
                dict.Add("album",      meta.ContainsKey("album")      ? meta["album"]?.ToString()      : " ");
                dict.Add("genre",      meta.ContainsKey("genre")      ? meta["genre"]?.ToString()      : " ");
                dict.Add("bpm",        meta.ContainsKey("bpm")        ? meta["bpm"]?.ToString()        : " ");
                dict.Add("duration",   meta.ContainsKey("duration")   ? meta["duration"]               : 0);
                dict.Add("time",       meta.ContainsKey("time")       ? meta["time"]                   : 0f);
                dict.Add("cover",      meta.ContainsKey("cover")      ? meta["cover"]?.ToString()      : " ");
                dict.Add("controls",   meta.ContainsKey("controls")   ? meta["controls"]               : null);
                dict.Add("performers", meta.ContainsKey("performers") ? meta["performers"]             : null);
            } else
                dict.Add("name", ""); // fallback

            return dict;
        }

        static int CheckTrackID(int id)
        {            
            if (id >= 0) return id;
            try
            {   
                throw new EngineErrorException(id);
            }
            catch (EngineErrorException e)
            {
                if (e.Error == -70)
                    Debug.LogWarning("Track timestamp has expired; please download a new version of the track. \nUpgrade your project for longer timestamp validity. License this track to remove timestamp restrictions.");
                else
                    Debug.LogError("Track validation failed: " + e.Message);
            }
            return -1;
        }

        public static List<Section> ParseBundle(string path)
        {
            string jsonText;
            if (Application.platform == RuntimePlatform.Android)
            {
                UnityEngine.Networking.UnityWebRequest www = UnityEngine.Networking.UnityWebRequest.Get(path + "/manifest.json");
                www.SendWebRequest();
                while (!www.isDone)
                {
                }
                jsonText = www.downloadHandler.text;
            }
            else
            {
                jsonText = File.ReadAllText(path + "/manifest.json");
            }

            List<ThemeInfo> themes = new List<ThemeInfo>();
            List<TrackInfo> tracks = new List<TrackInfo>();
            List<Section> sectionsList = new List<Section>();
            int idCount = 0;

            var json = MiniJSON.Json.Deserialize(jsonText) as Dictionary<string, object>;

            Dictionary<string, object> sections = (Dictionary<string, object>)json["sections"];
            foreach (KeyValuePair<string, object> sectionPair in sections)
            {
                Section s = new Section();
                s.name = sectionPair.Key;
                Dictionary<string, object> sectionData = sectionPair.Value as Dictionary<string, object>;

                List<object> themes_list = sectionData["themes"] as List<object>;
                for (int i = 0; i < themes_list.Count; i++)
                {
                    string thm = themes_list[i] as string;

                    ThemeInfo ti = new ThemeInfo();
                    ti.hash = thm;
                    Dictionary<string, object> trackInfoDict = ReadTrackMetadataFromPath(path, ti.hash);

                    ti.ID = -1;
                    idCount++;

                    ti.name = trackInfoDict["name"] as string;
                    ti.bundleID = System.IO.Path.GetFileName(path);

                    if (trackInfoDict["controls"] is List<object> controlsList)
                    {
                        foreach (var controlObject in controlsList)
                        {
                            if (controlObject is not Dictionary<string, object> control) continue;
                            
                            string name = control["name"].ToString();
                            string type = control["type"].ToString();
                            switch (type)
                            {
                                case "parameter":
                                    ti.macros.Add(name);
                                    break;
                                case "part":
                                    name = name.Replace("part: ", "");
                                    ti.parts.Add(name);
                                    break;
                                case "stinger":
                                    ti.stingers.Add(name);
                                    break;
                                case "playable":
                                    name = name.Replace("Playable Performer: ", "");
                                    ti.overridableInstruments.Add(name);
                                    break;
                            }
                        }
                    }

                    if (trackInfoDict["performers"] is List<object> performerList)
                    {
                        foreach (var performerObject in performerList)
                        {
                            if (performerObject is not Dictionary<string, object> performer) continue;
                            Performer p = new Performer();
                            
                            string name = performer["name"].ToString();
                            string lane = performer["lane_index"].ToString();
                            List<object> sinks = performer["sink_indices"] as List<object>;
                            
                            p.name = name;
                            p.lane_index = Convert.ToInt32(lane);
                            foreach (var sink in sinks) {
                                p.sink_indices.Add(Convert.ToInt32(sink));
                            }
                            ti.performerRoutings.Add(p);
                        }
                    }
                    themes.Add(ti);
                    s.themes.Add(ti);
                }

                List<object> playlists = sectionData["playlists"] as List<object>;
                foreach (var playlistObject in playlists)
                {
                    Dictionary<string, object> playlist = playlistObject as Dictionary<string, object>;
                    Playlist pl = new Playlist();
                    string playlistName = playlist["name"] as string;
                    pl.name = playlistName;

                    List<object> tracks_list = playlist["tracks"] as List<object>;
                    for (int i = 0; i < tracks_list.Count; i++)
                    {
                        string trck = tracks_list[i] as string;

                        TrackInfo ti = ParseTrack(path, trck);
                        idCount++;

                        pl.tracks.Add(ti);
                    }
                    s.playlists.Add(pl);
                }
                sectionsList.Add(s);
            }
            return sectionsList;
        }

        public static TrackInfo ParseTrack(string bundlePath, string trck)
        {
            TrackInfo ti = new TrackInfo();
            ti.hash = trck;
            ti.ID = -1;

            var trackDict = ReadTrackMetadataFromPath(bundlePath, ti.hash);
            ti.name = trackDict["name"].ToString();
            ti.artist = trackDict["artists"].ToString();
            ti.album = trackDict["album"].ToString();
            ti.genre = trackDict["genre"].ToString();
            ti.duration = int.Parse(trackDict["duration"].ToString());
            ti.time = float.Parse(trackDict["time"].ToString());
            ti.BPM = trackDict["bpm"].ToString();
            ti.bundleID = System.IO.Path.GetFileName(bundlePath);
            return ti;
        }

        public static async Task LoadTrackAssets(Engine engine, int trackid, string projectPath, bool loadAsync = true, bool streaming = false)
        {            
            List<Task> tasks = new List<Task>();
            for (int i = 0; i < engine.GetNumAssets(trackid); i++)
            {
                string id = engine.GetAssetId(trackid, i);
                string type = engine.GetAssetType(trackid, i);
                string uri = engine.GetAssetUri(trackid, i);

                if (loadAsync)
                    tasks.Add(Task.Run(() => SetAssetData(engine, trackid, id, uri, type, projectPath, streaming: streaming)));
                else
                    SetAssetData(engine, trackid, id, uri, type, projectPath, loadAsync: false, streaming: streaming);
            }

            await Task.WhenAll(tasks);
        }

        private static void SetAssetData(Engine engine, int trackid, string assetID, string uri, string type, string path, bool loadFromRemote = false, bool loadAsync = true, bool streaming = false)
        {
            path = path + "/" + uri;

            if (System.IO.File.Exists(uri)) path = uri;

            if (Application.platform == RuntimePlatform.Android)
                loadFromRemote = true;

            if (!loadFromRemote)
            {
                if (streaming)
                {                                    
                    engine.SetAssetPath(trackid, assetID, type);
                    return;
                }
                else
                {
                    byte[] data = File.ReadAllBytes(path);
                    if (data != null)
                    {
                        engine.SetAssetData(trackid, assetID, type, data, null);
                    }
                    data = null;
                }
            }
            else
            {
                if (Application.platform != RuntimePlatform.Android)
                {
                    path = "file://" + path;
                }
                path = path.Replace("#", "%23");

                ReactionalEngine.Instance.StartCoroutine(AsyncWebLoader(path, type, assetID, engine, trackid));
            }
        }

        private static IEnumerator AsyncWebLoader(string path, string type, string assetID, Engine engine, int trackid)
        {
            using (UnityWebRequest www = UnityWebRequest.Get(path))
            {
                var operation = www.SendWebRequest();
                yield return operation;

                bool requestValid = true;
                
#if UNITY_2020_3_OR_NEWER
                if (www.result == UnityWebRequest.Result.ConnectionError || www.result == UnityWebRequest.Result.ProtocolError)
#else
                if (!string.IsNullOrWhiteSpace(www.error))
#endif
                {
                    Debug.Log(www.error);                    
                    requestValid = false;
                }

                if (requestValid)
                {
                    byte[] data = www.downloadHandler.data;
                    if (data != null)
                    {
                        engine.SetAssetData(trackid, assetID, type, data, null);
                    }
                    data = null;
                }
            }
        }
    }
    
    /// <summary>
    /// Members of TrackInfo
    /// <list type="bullet">
    /// <item> public string name;</item>
    /// <item> public int ID;</item>
    /// <item> public string artist;</item>
    /// <item> public string album;</item>
    /// <item> public string genre;</item>
    /// <item> public string cover;</item>
    /// <item> public string BPM;</item>
    /// <item> public int duration;</item>
    /// <item> public float time;</item>
    /// <item> public string hash;</item>
    /// <item> public string bundleID;</item>
    /// </list>
    /// </summary>
    [Serializable]
    public class TrackInfo
    {
        public string name;
        public int ID;
        [HideInInspector] public string artist;
        [HideInInspector] public string album;
        [HideInInspector] public string genre;
        [HideInInspector] public string cover;
        [HideInInspector] public string BPM;
        [HideInInspector] public int duration;
        [HideInInspector] public float time;
        [HideInInspector] public string hash;
        [HideInInspector] public string bundleID;
    }
    
    /// <summary>
    /// Members of ThemeInfo
    /// <list type="bullet">
    /// <item> public string name;</item>
    /// <item> public int ID;</item>
    /// <item> public string artist;</item>
    /// <item> public string album;</item>
    /// <item> public string genre;</item>
    /// <item> public string cover;</item>
    /// <item> public string BPM;</item>
    /// <item> public int duration;</item>
    /// <item> public float time;</item>
    /// <item> public string hash;</item>
    /// <item> public string bundleID;</item>
    /// <item> public List&lt;string&gt; macros;</item>
    /// <item> public List&lt;string&gt; parts;</item>
    /// <item> public List&lt;string&gt; stingers;</item>
    /// <item> public List&lt;string&gt; playablePerformers;</item>
    /// </list>
    /// </summary>
    [Serializable]
    public class ThemeInfo : TrackInfo
    {
        public List<string> macros = new();
        public List<string> parts = new();
        public List<string> stingers = new();
        public List<string> overridableInstruments = new();
        public List<Performer> performerRoutings = new();
    }

    [Serializable]
    public class Performer
    {
        public string name;
        public int lane_index;
        public List<int> sink_indices = new();
    }
    
    /// <summary>
    /// Members of Bundle
    /// <list type="bullet">
    /// <item> public string name;</item>
    /// <item> public string path;</item>
    /// <item> public List&lt;Section&gt; sections;</item>
    /// </list>
    /// </summary>
    [Serializable]
    public class Bundle
    {
        [HideInInspector] public string name;
        [HideInInspector] public string path;
        public List<Section> sections = new List<Section>();
    }
    
    /// <summary>
    /// Members of Section
    /// <list type="bullet">
    /// <item> public string name;</item>
    /// <item> public List&lt;TrackInfo&gt; themes;</item>
    /// <item> public List&lt;Playlist&gt; playlists;</item>
    /// </list>
    /// </summary>
    [Serializable]
    public class Section
    {
        [HideInInspector] public string name;
        public List<ThemeInfo> themes = new List<ThemeInfo>();
        public List<Playlist> playlists = new List<Playlist>();
    }
    
    /// <summary>
    /// Members of PlayList
    /// <list type="bullet">
    /// <item> public string name;</item>
    /// <item> public List&lt;TrackInfo&gt; tracks;</item>
    /// </list>
    /// </summary>
    [Serializable]
    public class Playlist
    {
        [HideInInspector] public string name;
        public List<TrackInfo> tracks = new List<TrackInfo>();
    }
}
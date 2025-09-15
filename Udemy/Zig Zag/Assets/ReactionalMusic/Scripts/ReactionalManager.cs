using System.Collections.Generic;
using UnityEngine;
using System.IO;
using System.Linq;

namespace Reactional.Core
{
    [DefaultExecutionOrder(-100)]
    public class ReactionalManager : MonoBehaviour
    {
        public static ReactionalManager Instance
        {
            get
            {
                if (!_instance)
                {
#if UNITY_6000_0_OR_NEWER
                    _instance = FindFirstObjectByType<ReactionalManager>();
#else
                    _instance = FindObjectOfType<ReactionalManager>();
#endif
                }
                return _instance;
            }
        }
        private static ReactionalManager _instance;

        [Tooltip("The default section to load when the project starts. String.")]
        public string defaultSection = "";

        [SerializeField] public List<Bundle> bundles = new List<Bundle>();
        public List<ThemeInfo> _loadedThemes = new List<ThemeInfo>();
        public List<TrackInfo> _loadedTracks = new List<TrackInfo>();

        [Tooltip("Lookahead in microseconds. The higher the value, the more accurate the timing of the music will be. However, higher values will increase latency. Default is 100000.")]
        public int lookahead = 100_000;
        [HideInInspector] public int selectedTheme = 0;
        [HideInInspector] public int selectedTrack = 0;

        public enum PlaylistMode { Random, Sequential, Repeat, Single }

        [Tooltip("The mode in which the playlist will operate. Random, Sequential, Repeat, Single. Repeat will play the same track over and over again. Single will play the same track once until it is stopped.")]
        [SerializeField]
        private PlaylistMode _playlistMode = PlaylistMode.Sequential;

        [Tooltip("Load the music in the background or in the main thread. LoadInBackground is recommended for larger projects.")]
        [SerializeField]
#if !UNITY_ANDROID
        private Setup.LoadType _loadType = Setup.LoadType.LoadInBackground;
#else
        private Setup.LoadType _loadType = Setup.LoadType.Synchronous;
#endif

        public Reactional.Setup.LoadType loadType
        {
            get => _loadType;
            set => _loadType = value;
        }

        private float m_themeGain = 1;
        private float m_trackGain = 1;

        [HideInInspector] public bool isDucked;        

        public Setup.LoadType LoadType
        {
            get => _loadType;
            set => _loadType = value;
        }

        public float themeGain
        {
            get => m_themeGain;
            set
            {
                if (Reactional.Playback.MusicSystem.GetEngine() != null)
                    Reactional.Playback.Theme.Volume = value;
                m_themeGain = value;
            }
        }
        
        public float trackGain
        {
            get => m_trackGain;
            set
            {
                if (Reactional.Playback.MusicSystem.GetEngine() != null)
                    Reactional.Playback.Playlist.Volume = value;
                m_trackGain = value;
            }
        }

        public UnityEngine.Audio.AudioMixerGroup mainOut;
        
        private void Start()
        {
            if (Application.isPlaying)
            {            
                ReactionalEngine.Instance.output.outputAudioMixerGroup = mainOut;
                Reactional.Playback.Theme.Volume = m_themeGain;
                Reactional.Playback.Playlist.Volume = m_trackGain;
                ReactionalEngine.Instance.onAudioEnd += AudioEnd;                
            }
        }

        void OnEnable()
        {
            if (!Application.isPlaying)
            {
                UpdateBundles();
            }
        }

        void OnDisable()
        {
            if (Application.isPlaying)
                ReactionalEngine.Instance.onAudioEnd -= AudioEnd;
        }

        private void Awake()
        {
            if (!_instance)
            {
                _instance = this;
            }
            else
            {
                Destroy(this);
            }
        }

        public void UpdateBundles()
        {

            if (!Directory.Exists(Application.persistentDataPath + "/Reactional"))
            {
                Directory.CreateDirectory(Application.persistentDataPath + "/Reactional");
            }

            string[] folders = null;

            try
            {
                var persistentFolders = new string[0];
                var streamingFolders = new string[0];

                if (Directory.Exists(Application.persistentDataPath + "/Reactional"))
                {
                    persistentFolders = Directory.GetDirectories(Application.persistentDataPath + "/Reactional");
                    if (Application.platform == RuntimePlatform.Android)
                    {
                        for (int i = 0; i < persistentFolders.Length; i++)
                        {                            
                            persistentFolders[i] = "file://" + persistentFolders[i];
                        }
                    }
                }

                if (Directory.Exists(Application.streamingAssetsPath + "/Reactional"))
                {
                    streamingFolders = Directory.GetDirectories(Application.streamingAssetsPath + "/Reactional");
                }

                folders = persistentFolders.Concat(streamingFolders).ToArray();

                if (folders.Length == 0)
                {
                    Debug.LogWarning("Reactional: No bundles found in " + Application.persistentDataPath + "/Reactional or " + Application.streamingAssetsPath + "/Reactional");
                    Debug.LogWarning("Please visit https://app.reactionalmusic.com to get music content for your game.");
                    return;
                }
            }
            catch (System.Exception ex)
            {
                Debug.LogError("Error accessing directories: " + ex.Message);
                return;
            }

            
            if(Application.platform != RuntimePlatform.Android)
                bundles.Clear();
            _loadedTracks.Clear();
            _loadedThemes.Clear();

            foreach (string folder in folders)
            {
                Debug.Log("Loaded Reactional Bundle from path: " + folder);
                
                Bundle bundle = new Bundle();
                var contents = AssetHelper.ParseBundle(folder);
                bundle.name = Path.GetFileName(folder);
                bundle.path = folder;
                
                bundle.sections = contents;                
                bundles.Add(bundle);
            }
        }
        private void AudioEnd()
        {
            switch (_playlistMode)
            {
                case PlaylistMode.Random:
                    Reactional.Playback.Playlist.Random();
                    break;
                case PlaylistMode.Sequential:
                    Reactional.Playback.Playlist.Next();
                    break;
                case PlaylistMode.Repeat:
                    Reactional.Playback.Playlist.Play();
                    break;
                case PlaylistMode.Single:
                    break;
            }
        }
    }
}

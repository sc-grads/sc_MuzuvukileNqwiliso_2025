#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;
using System.Collections.Generic;
using Reactional.Core;
using Reactional.Playback;
using Playlist = Reactional.Playback.Playlist;
#if UNITY_2019_3_OR_NEWER
using UnityEngine.UIElements;
#endif

namespace Reactional.Editor
{
    public class ReactionalEditorTool : EditorWindow
    {
#if UNITY_2019_3_OR_NEWER
        public VisualTreeAsset visualTree;
        
        private IMGUIContainer playlistContainer;
        private IMGUIContainer themeContainer;
#endif
        
        private Vector2 scrollPosition;
        private Dictionary<string, (float controlValue, string controlType)> controls;

        [MenuItem("Tools/Reactional/Open Editor Tool", false, 888)]
        public static void ShowWindow() => GetWindow(typeof(ReactionalEditorTool), false, "Reactional Editor Tool");
        
        public void OnInspectorUpdate() => Repaint();

#if UNITY_2019_3_OR_NEWER
        private void CreateGUI()
        {
            visualTree.CloneTree(rootVisualElement);
            
            playlistContainer = rootVisualElement.Q<IMGUIContainer>("playlistContainer");
            playlistContainer.onGUIHandler = OnPlaylistGUI;
            
            themeContainer = rootVisualElement.Q<IMGUIContainer>("themeContainer");
            themeContainer.onGUIHandler = OnThemeGUI;
            
            rootVisualElement.Q<Button>("CustomizeYourMusicButton").clicked += () => {
                Application.OpenURL("https://app.reactionalmusic.com");
            };
        }
#endif

        private void OnEnable()
        {
            if (!ReactionalManager.Instance)
            {
                Debug.LogWarning("No ReactionalManager found in scene, please ensure one is present and re-open the editor tool.");
                
                var option = EditorUtility.DisplayDialogComplex(
                    title: "Welcome to Reactional",
                    message: "Would you like to add Reactional to the current scene?", 
                    ok: "Yes", cancel: "No", alt: "Don't show again"
                );
                if (option == 0) {
                    ReactionalEditor.AddReactionalManager();
                }
                return;
            }
            minSize = new Vector2(400, 600);
            if (ReactionalManager.Instance._loadedThemes.Count == 0) { return; }
            controls = Theme.GetControls();
        }
        
        private void OnPlaylistGUI()
        {
            if (!EditorApplication.isPlaying)
            {
                EditorGUILayout.LabelField("Please enter Play mode in the editor to enable track playback.");
                return;
            }
            EditorGUILayout.LabelField("Playback", EditorStyles.boldLabel);
            
            EditorGUILayout.BeginHorizontal();
            {
                var volume = EditorGUILayout.Slider("Volume", Playlist.Volume, 0.0f, 1.0f);
                Playlist.Volume = volume;
            }
            EditorGUILayout.EndHorizontal();
            
            EditorGUILayout.BeginHorizontal();
            {
                if (Playlist.GetTrackID() > 0)
                {
                    EditorGUILayout.LabelField("Current Track: " + Playlist.GetCurrentTrackInfo().name);
                }
                else
                {
                    EditorGUILayout.LabelField("Current Track: none");
                }
            }
            EditorGUILayout.EndHorizontal();
            
            // Play, Stop, Next, Previous buttons
            EditorGUILayout.BeginHorizontal();
            {
                if (GUILayout.Button("Previous")) { Playlist.Prev(); }
                
                if (Playlist.GetState() != MusicSystem.PlaybackState.Playing)
                {
                    if (GUILayout.Button("Play")) { Playlist.Play(); }
                }
                else
                {
                    if (GUILayout.Button("Stop")) { Playlist.Stop(); }
                }

                if (GUILayout.Button("Next")) { Playlist.Next(); }

                if (GUILayout.Button("Random")) { Playlist.Random(); }
            }
            EditorGUILayout.EndHorizontal();
            
            EditorGUILayout.Space();
            EditorGUILayout.LabelField("Loaded Tracks", EditorStyles.boldLabel);
            int trackcount = 0;
            
            EditorGUILayout.BeginHorizontal();
            {
                foreach (TrackInfo track in ReactionalManager.Instance._loadedTracks)
                {
                    if (GUILayout.Button(track.name)) { Playlist.PlayTrack(track); }
                    trackcount++;
                    if (trackcount % 3 == 0)
                    {
                        EditorGUILayout.EndHorizontal();
                        EditorGUILayout.BeginHorizontal();
                    }
                }
            }
            EditorGUILayout.EndHorizontal();
            EditorGUILayout.Space();
        }
        
        private void OnThemeGUI()
        {
            if (!EditorApplication.isPlaying)
            {
                EditorGUILayout.LabelField("Please enter Play mode in the editor to enable theme playback.");
                return;
            }
            
            if (controls == null)
            {
                if (ReactionalManager.Instance._loadedThemes.Count == 0)
                {
                    EditorGUILayout.LabelField("No themes loaded.");
                    return;
                }
                controls = Theme.GetControls();
            }
            
            EditorGUILayout.BeginHorizontal();
            {
                var volume = EditorGUILayout.Slider("Volume", Theme.Volume, 0.0f, 1.0f);
                Theme.Volume = volume;
            }
            EditorGUILayout.EndHorizontal();
            
            EditorGUILayout.BeginHorizontal();
            {
                if (ReactionalManager.Instance._loadedThemes.Count > 0)
                {
                    EditorGUILayout.LabelField("Current Theme: " + Theme.GetCurrentThemeInfo().name);
                }
                else
                {
                    EditorGUILayout.LabelField("Current Theme: none");
                    controls.Clear();
                    EditorGUILayout.EndHorizontal();
                    return;
                }
            }
            EditorGUILayout.EndHorizontal();
            
            EditorGUILayout.BeginHorizontal();
            {
                if (Theme.GetState() != MusicSystem.PlaybackState.Playing)
                {
                    if (GUILayout.Button("Play")) { Theme.Play(); }
                }
                else
                {
                    if (GUILayout.Button("Stop")) { Theme.Stop(); }
                }
            }
            EditorGUILayout.EndHorizontal();
            
            List<string> keysToUpdate = new List<string>();
            EditorGUILayout.LabelField("Macros", EditorStyles.boldLabel);
            foreach (KeyValuePair<string, (float controlValue, string controlType)> kvp in controls)
            {
                if (kvp.Value.controlType == "parameter")
                {
                    float newValue = EditorGUILayout.Slider(kvp.Key, kvp.Value.controlValue, 0.0f, 1.0f);

                    if (!Mathf.Approximately(newValue, kvp.Value.controlValue))
                    {
                        Theme.SetControl(kvp.Key, newValue);
                        keysToUpdate.Add(kvp.Key);
                    }
                }
            }
            foreach (string key in keysToUpdate)
            {
                controls[key] = ((float)Theme.GetControl(key), controls[key].controlType);
            }

            EditorGUILayout.Space();

            EditorGUILayout.LabelField("Stingers", EditorStyles.boldLabel);
            int count = 0;
            
            EditorGUILayout.BeginHorizontal();
            {
                foreach (KeyValuePair<string, (float controlValue, string controlType)> kvp in controls)
                {
                    if (kvp.Value.controlType == "stinger")
                    {
                        if (GUILayout.Button(kvp.Key)) { Theme.TriggerStinger(kvp.Key, 0.125f); }
                        count++;
                        if (count % 3 == 0)
                        {
                            EditorGUILayout.EndHorizontal();
                            EditorGUILayout.BeginHorizontal();
                        }
                    }
                }
            }
            EditorGUILayout.EndHorizontal();
            
            EditorGUILayout.Space();
            EditorGUILayout.LabelField("Parts", EditorStyles.boldLabel);
            int partcount = 0;
            
            EditorGUILayout.BeginHorizontal();
            {
                foreach (KeyValuePair<string, (float controlValue, string controlType)> kvp in controls)
                {
                    if (kvp.Value.controlType == "part")
                    {
                        if (GUILayout.Button(kvp.Key)) { Theme.SetControl(kvp.Key); }
                        partcount++;
                        if (partcount % 3 == 0)
                        {
                            EditorGUILayout.EndHorizontal();
                            EditorGUILayout.BeginHorizontal();
                        }
                    }
                }
            }
            EditorGUILayout.EndHorizontal();
            EditorGUILayout.Space();
        }

#if !UNITY_2019_3_OR_NEWER
        private void OnGUI()
        {
            var style = EditorStyles.inspectorDefaultMargins;
            style.margin = new RectOffset(8, 16, 8, 8);
            scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition, style);
            
            if (controls == null)
            {
                if (ReactionalManager.Instance._loadedThemes.Count == 0)
                {
                    EditorGUILayout.LabelField("No themes or tracks loaded. Please start playback in the editor.");
                    EditorGUILayout.EndScrollView();
                    return;
                }
                controls = Theme.GetControls();
            }

            // Define a custom style for the green button
            GUIStyle greenButtonStyle = new GUIStyle();
            Texture2D greenTexture = MakeTex(2, 2, new Color(0.0f, 1f, 0.0f, 1.0f));

            greenButtonStyle.normal.background = greenTexture;
            greenButtonStyle.hover.background = greenTexture;
            greenButtonStyle.active.background = greenTexture;
            greenButtonStyle.focused.background = greenTexture;
            greenButtonStyle.onNormal.background = greenTexture;
            greenButtonStyle.onHover.background = greenTexture;
            greenButtonStyle.onActive.background = greenTexture;
            greenButtonStyle.onFocused.background = greenTexture;
            greenButtonStyle.normal.textColor = Color.black;
            greenButtonStyle.fontSize = 14;
            greenButtonStyle.fontStyle = FontStyle.Bold;
            greenButtonStyle.alignment = TextAnchor.MiddleCenter;
            greenButtonStyle.padding = new RectOffset(4, 4, 4, 4);

            // MAKE A BIG FAT GREEN BUTTON FOR CUSTOMIZATION OF MUSIC THAT TAKES YOU TO A WEBSITE
            if (GUILayout.Button("Customize Music", greenButtonStyle))
            {
                Application.OpenURL("https://app.reactionalmusic.com");
            }
            
            //_________________________________________
            EditorGUILayout.LabelField("Playlist Controls", EditorStyles.boldLabel);
            OnPlaylistGUI();
            
            //________________________________________
            EditorGUILayout.LabelField("Theme Controls", EditorStyles.boldLabel);
            OnThemeGUI();
            
            EditorGUILayout.Space();

            int[] barbeat = ReactionalEngine.Instance.CurrentBarBeat;
            EditorGUILayout.LabelField(barbeat[0].ToString(), EditorStyles.boldLabel);
            EditorGUILayout.LabelField(barbeat[1].ToString(), EditorStyles.boldLabel);

            EditorGUILayout.EndScrollView();
        }
        
        private Texture2D MakeTex(int width, int height, Color col)
        {
            Color[] pix = new Color[width * height];
            for (int i = 0; i < pix.Length; i++)
            {
                pix[i] = col;
            }
            Texture2D result = new Texture2D(width, height);
            result.SetPixels(pix);
            result.Apply();
            return result;
        }
#endif
    }
}
#endif

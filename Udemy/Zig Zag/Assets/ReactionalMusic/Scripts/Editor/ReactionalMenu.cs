#if UNITY_EDITOR
using System.IO;
using Reactional.Core;
using UnityEditor;
using UnityEngine;

namespace Reactional.Editor
{
    [InitializeOnLoad]
    public class ReactionalEditor : MonoBehaviour
    {
        private const string dontAskAgainKey = "Reactional.DontShowAgain";
        private const string firstTimeKey = "Reactional.FirstTime";
        private static bool firstTime = true;

        static ReactionalEditor()
        {
            var reactionalAssetsPath = $"{Application.streamingAssetsPath}/Reactional";

            // check if folder exists, otherwise create it
            if (!Directory.Exists(reactionalAssetsPath)) Directory.CreateDirectory(reactionalAssetsPath);

            EditorApplication.projectChanged += CheckManager;
        }

        private static void CheckManager()
        {
            if (firstTime && EditorPrefs.GetBool(Application.productName + "." + dontAskAgainKey, true))
            {
                //EditorPrefs.SetBool(firstTimeKey, false);
#if UNITY_6000_0_OR_NEWER
                var rm = FindFirstObjectByType<ReactionalManager>();
#else
                var rm = FindObjectOfType<ReactionalManager>();
#endif
                if (rm == null)
                {
                    var option = EditorUtility.DisplayDialogComplex("Welcome to Reactional",
                        "Would you like to add Reactional to the current scene?", "Yes", "No", "Don't show again");
                    switch (option)
                    {
                        case 0:
                            AddReactionalManager();
                            break;
                        case 2:
                            EditorPrefs.SetBool(Application.productName + "." + dontAskAgainKey, false);
                            break;
                    }
                }
            }
            firstTime = false;
        }

        [MenuItem("Tools/Reactional/Add Reactional Manager", false, 889)]
        public static void AddReactionalManager()
        {
#if UNITY_6000_0_OR_NEWER
            var rm = FindFirstObjectByType<ReactionalManager>();
#else
            var rm = FindObjectOfType<ReactionalManager>();
#endif
            if (rm != null)
            {
                Debug.LogWarning("Reactional Manager already exists in the scene.");
                return;
            }

            // Create the Reactional Music GameObject and add the ReactionalManager and BasicPlayback components
            var reactionalMusic = new GameObject("Reactional Music");
            reactionalMusic.AddComponent<ReactionalManager>();
            reactionalMusic.AddComponent<BasicPlayback>();

            // Create the Reactional Engine child GameObject and add the ReactionalEngine script
            var reactionalEngine = new GameObject("Reactional Engine");
            reactionalEngine.AddComponent<ReactionalEngine>();
            reactionalEngine.transform.SetParent(reactionalMusic.transform);
        }

        [MenuItem("Tools/Reactional/Visit Platform", false, 60)]
        private static void OpenReactionalPlatform() => Application.OpenURL("https://app.reactionalmusic.com/");

        [MenuItem("Tools/Reactional/Documentation", false, 61)]
        private static void OpenReactionalDocumentation() => Application.OpenURL("https://docs.reactionalmusic.com/Unity/");

        [MenuItem("Tools/Reactional/Discord", false, 62)]
        private static void OpenReactionalDiscord() => Application.OpenURL("https://discord.gg/bAJNRdXq4c");

        [MenuItem("Tools/Reactional/Forum Support", false, 63)]
        private static void OpenReactionalSupport() => Application.OpenURL("https://forum.reactionalmusic.com/");

        [MenuItem("Tools/Reactional/Reactional Website", false, 64)]
        private static void OpenReactionalWebsite() => Application.OpenURL("https://reactionalmusic.com/");

        private static void ShowDownloadMessage(string assetName, string url)
        {
            var confirm = EditorUtility.DisplayDialog(
                "Downloading " + assetName,
                assetName + " will be downloaded in your browser.\n\nOnce it's done, open it as a separate Unity project.",
                "OK"
            );
            if (confirm) Application.OpenURL(url);
        }

        [MenuItem("Tools/Reactional/Demos & Games/Download Reactional Demo Scene", false, 104)]
        private static void DownloadDemoScene()
        {
            const string DemoSceneUrl = "https://storage.googleapis.com/rm-cdn/demo-scenes/unity/ReactionalShooterDemo.zip";
            ShowDownloadMessage("Reactional Demo Scene", DemoSceneUrl);
        }
        
        [MenuItem("Tools/Reactional/Demos & Games/Download Reactional Disco Bot Scene", false, 105)]
        private static void DownloadDiscoBot()
        {
            const string DiscoBotUrl = "https://storage.googleapis.com/rm-cdn/demo-scenes/unity/ReactionalDiscoBot.zip";
            ShowDownloadMessage("Reactional Disco Bot", DiscoBotUrl);
        }

        [MenuItem("Tools/Reactional/Open Readme", false, 106)]
        private static void OpenReadMe() => OpenFile("README.md");

        [MenuItem("Tools/Reactional/Open Changelog", false, 107)]
        private static void OpenChangelog() => OpenFile("CHANGELOG.md");
        
        [MenuItem("Tools/Reactional/Version: " + Reactional.Setup.PluginVersion, false, 999)]
        private static void Version() {}
        [MenuItem("Tools/Reactional/Version: " + Reactional.Setup.PluginVersion, true, 999)]
        private static bool DisableVersion() { return false; }

        private static void OpenFile(string fileName)
        {
            const string PluginFolder = "ReactionalMusic";
            const string Resources = "Resources";
            var filePath = Path.Combine(Application.dataPath, PluginFolder, Resources, fileName);

            if (File.Exists(filePath)) {
                EditorUtility.OpenWithDefaultApp(filePath);
            } else {
                EditorUtility.DisplayDialog(
                    title: "File Not Found",
                    message: $"Could not find {fileName} in {PluginFolder}.",
                    ok: "OK"
                );
            }
        }
    }
}
#endif
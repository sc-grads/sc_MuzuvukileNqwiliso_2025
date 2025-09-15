#if UNITY_EDITOR

using System;
using UnityEngine;
using UnityEditor;
using UnityEngine.Analytics;

namespace Reactional.VSAttribution
{
	[InitializeOnLoad]
	public class AttributionPopup : MonoBehaviour
	{
		static AttributionPopup()
		{
			EditorApplication.projectChanged += FirstTimePopup;
		}
		static void FirstTimePopup()
		{
			if (!EditorPrefs.GetBool(Application.productName + "." + "vsp_validated"))
			{
				Vector2 s_WindowSize = new Vector2(360, 408);
				var window = RegisterPlugin.GetWindow<RegisterPlugin>();

				window.titleContent = new GUIContent("Reactional - Validate");
				window.minSize = s_WindowSize;
				window.maxSize = s_WindowSize;
			}
			else
			{
				EditorApplication.projectChanged -= FirstTimePopup;
			}
		}
	}

	public class RegisterPlugin : EditorWindow
	{
		static readonly Vector2 s_WindowSize = new Vector2(360, 408);

		public string actionName = "Register";
		public string partnerName = "ReactionalMusic";
		public string customerUid;

		public string customerEmail = "";

		[MenuItem("Tools/Reactional/Validate", false, 200)]
		public static void Initialize()
		{
			var window = GetWindow<RegisterPlugin>();

			window.titleContent = new GUIContent("Reactional - Validate");
			window.minSize = s_WindowSize;
			window.maxSize = s_WindowSize;
		}

		public void OnGUI()
		{
			const int uniformPadding = 16;
			var padding = new RectOffset(uniformPadding, uniformPadding, uniformPadding, uniformPadding);
			var area = new Rect(padding.right, padding.top, position.width - (padding.right + padding.left), position.height - (padding.top + padding.bottom));

			GUILayout.BeginArea(area);
			{
				GUILayout.Space(16f);
				GUILayout.Label((Texture2D)Resources.Load("ReactionalLogo"));
				GUILayout.Space(16f);

				if (!EditorPrefs.GetBool(Application.productName + "." + "vsp_validated", false))
				{
					GUILayout.Label("Enter the same e-mail that was used to sign up to\nthe Reactional Platform.");
					GUILayout.Space(8f);

					GUILayout.Label("E-mail: ", EditorStyles.boldLabel);
					customerEmail = GUILayout.TextField(customerEmail);

					GUILayout.Space(16f);

					if (GUILayout.Button("Validate"))
					{
						if (customerEmail == "")
						{
							Debug.Log($"[Reactional Music] No e-mail address entered!");
						}
						else
						{
							customerUid = customerEmail;
							var result = ReactionalVSAttribution.SendAttributionEvent(actionName, partnerName, customerUid);
							Debug.Log($"[Reactional Music] Validation status: {result}!");
							if (result == UnityEngine.Analytics.AnalyticsResult.Ok)
							{
								EditorPrefs.SetBool(Application.productName + "." + "vsp_validated", true);
								Close();
							}
						}
					}
				}
				else
				{
					GUILayout.Label("You have already validated your account.");
					GUILayout.Space(8f);
					if (GUILayout.Button("Close"))
					{
						Close();
					}
				}
			}
			GUILayout.EndArea();
		}
	}

	public static class ReactionalVSAttribution
	{
		const int k_VersionId = 4;
		const int k_MaxEventsPerHour = 10;
		const int k_MaxNumberOfElements = 1000;

		const string k_VendorKey = "unity.vsp-attribution";
		const string k_EventName = "vspAttribution";

#if UNITY_2023_2_OR_NEWER
		[AnalyticInfo(eventName: k_EventName, vendorKey: k_VendorKey, maxEventsPerHour: k_MaxEventsPerHour, maxNumberOfElements: k_MaxNumberOfElements, version: k_VersionId)]
		private class VSAttributionAnalytic : IAnalytic
		{
			private VSAttributionData _data;
			
			public VSAttributionAnalytic(VSAttributionData data)
			{
				_data = data;
			}

			public bool TryGatherData(out IAnalytic.IData data, out Exception error)
			{
				error = null;
				data = _data;
				return data != null;
			}
		}
#else
		static bool RegisterEvent()
		{
			AnalyticsResult result = EditorAnalytics.RegisterEventWithLimit(k_EventName, k_MaxEventsPerHour,
				k_MaxNumberOfElements, k_VendorKey, k_VersionId);

			var isResultOk = result == AnalyticsResult.Ok;
			return isResultOk;
		}
#endif

		[Serializable]
		struct VSAttributionData
#if UNITY_2023_2_OR_NEWER
			: IAnalytic.IData
#endif
		{
			public string actionName;
			public string partnerName;
			public string customerUid;
			public string extra;
		}

		/// <summary>
		/// Registers and attempts to send a Verified Solutions Attribution event.
		/// </summary>
		/// <param name="actionName">Name of the action, identifying a place this event was called from.</param>
		/// <param name="partnerName">Identifiable Verified Solutions Partner's name.</param>
		/// <param name="customerUid">Unique identifier of the customer using Partner's Verified Solution.</param>
		public static AnalyticsResult SendAttributionEvent(string actionName, string partnerName, string customerUid)
		{
			try
			{
				// Are Editor Analytics enabled ? (Preferences)
				if (!EditorAnalytics.enabled)
					return AnalyticsResult.AnalyticsDisabled;

#if !UNITY_2023_2_OR_NEWER
				if (!RegisterEvent())
					return AnalyticsResult.InvalidData;
#endif
				// Create an expected data object
				var eventData = new VSAttributionData
				{
					actionName = actionName,
					partnerName = partnerName,
					customerUid = customerUid,
					extra = "{}"
				};
#if UNITY_2023_2_OR_NEWER
				VSAttributionAnalytic analytic = new VSAttributionAnalytic(eventData);
				return EditorAnalytics.SendAnalytic(analytic);
#else
				return EditorAnalytics.SendEventWithLimit(k_EventName, eventData, k_VersionId);
#endif
			}
			catch
			{
				// Fail silently
				return AnalyticsResult.AnalyticsDisabled;
			}
		}
	}
}
#endif
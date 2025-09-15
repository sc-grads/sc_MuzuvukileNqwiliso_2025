using UnityEngine;
using System.Threading;
using Reactional.Playback;

namespace Reactional.Core
{
    [RequireComponent(typeof(AudioSource))]
    [DefaultExecutionOrder(1000)]
    public class ReactionalEngine : MonoBehaviour
    {
        public static ReactionalEngine Instance { get; private set; }

        public Engine engine;
        [HideInInspector] public bool _allowPlay;
        public bool _outputEvents = true;
        private int _sampleRate;
        private float tempo_bpm;
        private int tempo_microbeats;
        private float currentBeat;
        private int _currentRootNote;
        private float[] _currentScale;
        private int[] _currentBarBeat = new int[2];
        public float TempoBpm => tempo_bpm;
        public float CurrentBeat => currentBeat;
        public int CurrentRootNote => _currentRootNote;
        public float[] CurrentScale => _currentScale;
        public int[] CurrentBarBeat => _currentBarBeat;

        private int _resample_quality = 2;

        public int ResampleQuality
        {
            get => _resample_quality;
            set => _resample_quality = value;
        }
        
        [SerializeField] public bool enableLogging = true;

        private bool _AudioUpdateMode = false;
        private bool _threadedUpdateMode = true;
        private int _beatIndex = 3;
        [HideInInspector] public AudioSource output;

        #region Delegates

        public delegate void NoteOnEvent(double offset, int sink, int lane, float pitch, float velocity);

        public delegate void NoteOffEvent(double offset, int sink, int lane, float pitch, float velocity);

        public delegate void StingerEvent(double offset, bool startevent, int stingerOrigin);

        public delegate void AudioPlayEvent();
        
        public delegate void AudioEndEvent();

        public delegate void BarBeatEvent(double offset, int bar, int beat);
        
        public delegate void QuantizationEvent();

        #endregion

        #region Events

        OSCMessage[] events;
        public NoteOnEvent onNoteOn;
        public NoteOffEvent onNoteOff;
        public StingerEvent stingerEvent;
        public AudioPlayEvent onAudioPlay;
        public AudioEndEvent onAudioEnd;
        public BarBeatEvent onBarBeat;
        
        public struct QuantizationEventData
        {
            public QuantizationEvent Event;
            public int LastQuant;
        }
        private const int QUANT_EVENT_COUNT = 15;
        public readonly QuantizationEventData[] quantization_events = new QuantizationEventData[QUANT_EVENT_COUNT];

        #endregion

        [SerializeField] private Reactional.Setup.UpdateMode _updateMode = Reactional.Setup.UpdateMode.Threaded;

        public Reactional.Setup.UpdateMode UpdateMode
        {
            get => _updateMode;
            set => _updateMode = value;
        }

        [SerializeField]
        public Reactional.Setup.AudioOutputMode _audioOutputMode = Reactional.Setup.AudioOutputMode.Unity;

        public Reactional.Setup.AudioOutputMode AudioOutputMode
        {
            get => _audioOutputMode;
            set => _audioOutputMode = value;
        }

        void Awake()
        {
            engine = new Engine();            
            if (_audioOutputMode == Reactional.Setup.AudioOutputMode.Unity)
                _sampleRate = AudioSettings.outputSampleRate;
            output = GetComponent<AudioSource>();

            if (!Instance)
                Instance = this;
        }

        private Thread thread;

        void Start()
        {
            switch (_updateMode)
            {
                case Reactional.Setup.UpdateMode.Threaded:
                    _threadedUpdateMode = true;
                    _AudioUpdateMode = false;
                    break;
                case Reactional.Setup.UpdateMode.AudioThread:
                    _threadedUpdateMode = false;
                    _AudioUpdateMode = true;
                    break;
                case Reactional.Setup.UpdateMode.Main:
                    _threadedUpdateMode = false;
                    _AudioUpdateMode = false;
                    break;
                default:
                    break;
            }

            if (_threadedUpdateMode)
            {
                _AudioUpdateMode = false;
                thread = new Thread(DoWork);
                thread.Start();
            }
        }

        void DoWork()
        {
            while (true)
            {
                if (_allowPlay)
                    Process();
                Thread.Sleep(16); // 60fps
            }
        }

        void OnDestroy()
        {
            if (thread != null && thread.IsAlive)
                thread.Abort();
        }

        private void Update()
        {
            if (engine == null || !_allowPlay) return;
            GetEvents(-1);            
            if (!_AudioUpdateMode && !_threadedUpdateMode) Process();
        }

        void OnAudioFilterRead(float[] data, int channels)
        {
            if (_audioOutputMode != 0)
            {
                return;
            }

            int frames = data.Length / channels;
            if (_allowPlay && engine != null)
            {
                engine.RenderInterleaved(_sampleRate, frames, channels, data);
                if (_AudioUpdateMode && !_threadedUpdateMode) Process();
            }
        }

        private void Process()
        {
            engine.Process(-1);
            int theme = engine.GetTheme();
            if (theme >= 0)
            {
                currentBeat = (float)engine.GetParameterFloat(theme, _beatIndex) / 1000000f;
                tempo_bpm = (float)engine.GetParameterFloat(theme, engine.FindParameter(theme, "bpm"));
            }
        }

        private void OnEnable()
        {
            onNoteOn += RouteNoteOn;
            onNoteOff += RouteNoteOff;
            stingerEvent += RouteStingerEvent;
            onBarBeat += RouteBarBeat;
        }

        private void OnDisable()
        {
            onNoteOn -= RouteNoteOn;
            onNoteOff -= RouteNoteOff;
            stingerEvent -= RouteStingerEvent;
            onBarBeat -= RouteBarBeat;
            _allowPlay = false;
        }

        private void GetEvents(int trackid)
        {
            /* REACTIONAL OSC EVENTS
             *
             * We can easily intercept the events generated from the reactional system by polling from the OSC queue.
             * Reactional uses communication via the OSC protocol between internal subsystems.
             * This has an added benefit in that we can listen in on said communication, and also communicate directly
             * with the various features, as a sort of low level API.
             *
             * The most common use case would be to listen for "noteon", and "noteoff" messages generated by the engine.
             */

            long startBeat = 0;
            events = engine.Poll(trackid, ref startBeat);
            bool gotScale = false, gotRoot = false, gotBar = false;

            if (!_outputEvents) return;

            var len = events?.Length ?? -1;
            for (int i = 0; i < len; i++)
            {
                OSCMessage val = events![i];
                switch (val.Address)
                {
                    case "/noteon":
                        onNoteOn?.Invoke(
                            offset: (long)val[0] / 1_000_000.0d,  // 0    h microbeats
                            sink: (int)val[1],                    // 1    i sink index  (a sink is the origin of the events)
                            lane: (int)val[2],                    // 2    i output/group index
                            pitch: (float)val[3],                 // 3    f pitch
                            velocity: (float)val[4]               // 4    f velocity 
                        );
                        break;

                    case "/noteof":
                        onNoteOff?.Invoke(
                            offset: (long)val[0] / 1_000_000.0d,  // 0    h microbeats
                            sink: (int)val[1],                    // 1    i sink index  (a sink is the origin of the events)
                            lane: (int)val[2],                    // 2    i output/group index
                            pitch: (float)val[3],                 // 3    f pitch
                            velocity: (float)val[4]               // 4    f velocity 
                        );
                        break;
                    
                    case "/audio/play":
                        onAudioPlay?.Invoke();
                        break;
                    
                    case "/audio/end":
                        onAudioEnd?.Invoke();
                        break;

                    case "/scale":
                        if ((int)val[2] != -1 || gotScale)
                            continue;
                        
                        string scale = (string)val[4];
                        string[] scaleArray = scale.Split(' ');

                        _currentScale = new float[scaleArray.Length];
                        for (int j = 1; j < scaleArray.Length; j++)
                        {
                            _currentScale[j] = float.Parse(scaleArray[j]);
                        }
                        gotScale = true;
                        break;

                    case "/root":
                        if ((int)val[2] == -1 || gotRoot)
                            continue;
                            
                        _currentRootNote = (int)(float)val[3];
                        gotRoot = true;
                        break;

                    case "/bar":
                        if (gotBar)
                            continue;
                            
                        onBarBeat?.Invoke(
                            offset: ((long)(val[0]) / 1_000_000.0d), // 0    h microbeats
                            bar: (int)(val[3]),                      // 3    i bar
                            beat: (int)(val[4])                      // 4    i beat
                        );
                        _currentBarBeat[0] = (int)val[3];
                        _currentBarBeat[1] = (int)val[4];
                        gotBar = true;

                        break;
                    
                    case "/stinger/start":
                        stingerEvent?.Invoke(
                            offset: ((long)(val[0]) / 1_000_000.0d), // 0    h microbeats
                            startevent: true,
                            stingerOrigin: (int)(val[3])             // 3    i stinger origin
                        );
                        break;
                    
                    case "/stinger/stop":
                        stingerEvent?.Invoke(
                            offset: ((long)(val[0]) / 1_000_000.0d), // 0    h microbeats
                            startevent: false,
                            stingerOrigin: (int)(val[3])             // 3    i stinger origin
                        );
                        break;
                    default:
                        break;
                }
            }

            events = null;
            
            var microbeat = MusicSystem.GetCurrentMicroBeat();
            for(var i = 0; i < QUANT_EVENT_COUNT; i++)
            {
                ref var quantizationEventData = ref quantization_events[i];
                ref var quantEvent = ref quantizationEventData.Event;
                ref var lastQuant = ref quantizationEventData.LastQuant;
                
                if (quantEvent == null) { continue; }
                
                var quant = MusicSystem.QuantToDouble((MusicSystem.Quant)i) * 1_000_000;
                if(lastQuant > microbeat && microbeat > 0) { lastQuant = (int)(Mathf.Ceil((float)(microbeat / quant)) * quant); }
                if(lastQuant <= 0) { lastQuant = (int)(Mathf.CeilToInt((float)(microbeat / quant)) * quant); continue; }
                if(microbeat >= lastQuant)
                {
                    lastQuant = (int)(Mathf.CeilToInt((float)(microbeat / quant)) * quant);
                    quantEvent.Invoke();
                }
            }
        }

        #region Event Handlers

        private void RouteNoteOn(double beat, int sink, int lane, float pitch, float velocity)
        {
        }

        private void RouteNoteOff(double beat, int sink, int lane, float pitch, float velocity)
        {
        }

        private void RouteStingerEvent(double beat, bool startevent, int stingerOrigin)
        {
        }

        private void RouteAudioEnd()
        {
        }

        private void RouteBarBeat(double offset, int bar, int beatIndex)
        {
        }

        #endregion
    }
}

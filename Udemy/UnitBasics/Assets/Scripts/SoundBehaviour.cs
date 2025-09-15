using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class SoundBehaviour : MonoBehaviour
{  
    public AudioSource musicSource;
    
    // Update is called once per frame
    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Space))
        {
            if (musicSource)
            {
                if (musicSource.isPlaying)
                {
                    musicSource.Pause();
                }
                else
                {
                    musicSource.Play();
                }
            }
              
        }
    }
}

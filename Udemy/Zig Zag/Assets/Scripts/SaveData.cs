using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class SavePlayerData : MonoBehaviour
{

    int number = 0;
    // Start is called before the first frame update
    void Start()
    {
        Debug.Log("Saved Number: " + GetNumber());
    }

    // Update is called once per frame
    void Update()
    {
        if(Input.GetKeyDown(KeyCode.Space))
        {
            number++;
           if(number > GetNumber())
            {
                // Here we save the number in PlayerPrefs
                PlayerPrefs.SetInt("MyNumber", number);
            }
            Debug.Log("Number: " + number);
            Debug.Log("Saved Number: " + GetNumber());
        }
    }

    int GetNumber()
    {
        // This will get the number saved in PlayerPrefs, or return 0 if it doesn't exist
        int myNumber = PlayerPrefs.GetInt("MyNumber", 0);
        return myNumber;
    }
}

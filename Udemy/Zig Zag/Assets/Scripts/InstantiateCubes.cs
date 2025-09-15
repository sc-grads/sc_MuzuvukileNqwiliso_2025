using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class InstantiateCubes : MonoBehaviour
{
    public Transform prefb;
    //void Start()
    //{
    //    for (int i = 0; i < 10; i++)
    //    {
    //        for (int j = 0; j < 10; j++)
    //        {
    //            Instantiate(prefb, new Vector3(i * 2.0F, 0, j * 2.0F), Quaternion.identity);
    //        }
    //    }
    //}

    private void Start()
    {
        InvokeRepeating("CreateCube", 2.0f, 1.0f);
    }

    private int Counter = 0;

    // Update is called once per frame
    public void CreateCube()
    {
        if (Input.GetKeyDown(KeyCode.Space))
        {

            if (Counter < 10)
            {
                Instantiate(prefb, new Vector3(Counter * 2.0F, 0, 0), Quaternion.identity);
                Counter++;
                print(Counter);
            }
            else
            {
                CancelInvoke("CreateCube");
            }

        }

    }
}

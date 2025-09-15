using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CheckForObject : MonoBehaviour
{

    void Update()
    {
        RaycastHit raycastHit;
        Ray ray = Camera.main.ScreenPointToRay(Input.mousePosition);

        if (Physics.Raycast(ray, out raycastHit))
        {
            print("Mouse is pointing at: " + raycastHit.collider.gameObject.name);
        }


        //if(Physics.Raycast(transform.position, -Vector3.up, out raycastHit, 100f))
        //{
        //    print("We have hit: " + raycastHit.collider.gameObject.name+ " and it's possion is at : "+ raycastHit.distance);
        //}else
        //{
        //    print("We have not hit anything");
        //}
    }
}

using System.Collections;
using System.Collections.Generic;
using Unity.VisualScripting;
using UnityEngine;

public class RockerPlayer1 : MonoBehaviour
{
    public float moveSpeed;

    void FixedUpdate()
    {
        float verticalInput = Input.GetAxis("Vertical");
        Vector2 movement = new Vector2(0, verticalInput) * moveSpeed;
        GetComponent<Rigidbody2D>().velocity = movement;
    }

}


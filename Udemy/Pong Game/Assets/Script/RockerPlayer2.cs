using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class RockerPlayer2 : MonoBehaviour
{
    public float moveSpeed;

    void FixedUpdate()
    {
        float verticalInput = Input.GetAxis("Vertical2");
        Vector2 movement = new Vector2(0, verticalInput) * moveSpeed;
        GetComponent<Rigidbody2D>().velocity = movement;
    }

}

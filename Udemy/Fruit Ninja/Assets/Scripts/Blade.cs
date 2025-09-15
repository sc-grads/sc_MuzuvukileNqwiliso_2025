using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Blade : MonoBehaviour
{
    private Rigidbody2D rb;
    private Collider2D col;

    public float minVelo = 0.1f;

    private Vector3 lastMousePos;

    void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
        col = GetComponent<Collider2D>();
    }

    void Update()
    {
        Vector3 mouseWorldPos = GetMouseWorldPosition();

        // Check movement *before* updating rb position
        col.enabled = IsMouseMoving(mouseWorldPos);

        // Move blade to mouse
        rb.position = mouseWorldPos;
    }

    private Vector3 GetMouseWorldPosition()
    {
        Vector3 mousePos = Input.mousePosition;
        mousePos.z = Mathf.Abs(Camera.main.transform.position.z); 
        return Camera.main.ScreenToWorldPoint(mousePos);
    }

    private bool IsMouseMoving(Vector3 currentMousePos)
    {
        float traveled = (lastMousePos - currentMousePos).magnitude;
        lastMousePos = currentMousePos;

        return traveled > minVelo;
    }
}

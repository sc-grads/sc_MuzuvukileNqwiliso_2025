using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class FollowCam : MonoBehaviour
{
   public Transform target; // The target for the camera to follow
 private Vector3 offset; // Offset from the target position
    public float smoothSpeed = 0.125f; // Speed of the camera smoothing

    private void Awake()
    {
        offset = transform.position - target.position; // Calculate initial offset

    }

    private void LateUpdate()
    {
        Vector3 desiredPosition = target.position + offset; // Desired position based on target and offset
        Vector3 smoothedPosition = Vector3.Lerp(transform.position, desiredPosition, smoothSpeed); // Smoothly interpolate to the desired position
        transform.position = smoothedPosition; // Update camera position
        transform.LookAt(target); // Optional: Make the camera look at the target
    }
}

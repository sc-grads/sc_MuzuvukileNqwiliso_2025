using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class PlayerMovement : MonoBehaviour
{
    public GameObject crystalEffect;
    public Transform rayStart;
    private Animator animator;
    private Rigidbody rb;
    private bool isWalkingRight = true;

    private GameManager game;
    private AudioSource audioSource;

    private void Awake()
    {
        rb = GetComponent<Rigidbody>();
        animator = GetComponent<Animator>();
        game = FindObjectOfType<GameManager>();
        audioSource = GetComponent<AudioSource>();
    }

    private void FixedUpdate()
    {
        if (!game.hasGameStarted)
        {
            return;
        }
        else
        {
            animator.SetTrigger("HasStarted");
        }

        rb.transform.position = transform.position + transform.forward * 2 * Time.deltaTime;
    }

    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.Space))
        {
            SwitchDirection();
        }

        if (Input.GetKeyDown(KeyCode.Escape))
        {
            game.ResetHighScore();
        }

        RaycastHit raycastHit;
        if (!Physics.Raycast(rayStart.position, -transform.up, out raycastHit, Mathf.Infinity))
        {
            animator.SetTrigger("OnFalling");
        }else
        {
            animator.SetTrigger("NotCallingAnyMore");
        }

        if (transform.position.y < -2)
        {
            game.EndGame();
        }
    }

    private void SwitchDirection()
    {
        if (!game.hasGameStarted)
        {
            return;
        }

        isWalkingRight = !isWalkingRight;
        if (isWalkingRight)
        {
            transform.rotation = Quaternion.Euler(0, 45, 0);
        }
        else
        {
            transform.rotation = Quaternion.Euler(0, -45, 0);
        }
    }

    private void OnTriggerEnter(Collider other)
    {
        if (other.CompareTag("Crystal"))
        {
            game.IncreaseScore();

            if (audioSource != null)
                audioSource.Play();

            GameObject g = Instantiate(crystalEffect, rayStart.transform.position, Quaternion.identity);
            Destroy(g, 0.50f);

            Destroy(other.gameObject);
        }
    }
}

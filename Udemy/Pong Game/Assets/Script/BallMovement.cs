using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class BallMovement : MonoBehaviour
{
    public float speed;
    public float extraSpeed;
    public float maxSpeed;

    int hitCounter = 0;

    void Start()
    {
        StartCoroutine(StartBall());
    }


    void PositionBalll(bool isStartPlayer1)
    {
        this.GetComponent<Rigidbody2D>().velocity = new Vector2(0, 0);

       if (isStartPlayer1)
            this.gameObject.transform.localPosition = new Vector3(-100, 0, 0);
        else
            this.gameObject.transform.localPosition = new Vector3(100, 0,0);
    }

    public IEnumerator StartBall(bool isStartPlayer1 = true)
    {
        this.PositionBalll(isStartPlayer1);
        hitCounter = 0;
        yield return new WaitForSeconds(2);

        if (isStartPlayer1)
            MoveBall(new Vector2(1, 0));
        else
            MoveBall(new Vector2(-1, 0));
    }

    public void MoveBall(Vector2 dir)
    {
        dir = dir.normalized;
        float currentSpeed = Mathf.Min(speed + (hitCounter * extraSpeed), maxSpeed);

        Rigidbody2D rb = GetComponent<Rigidbody2D>();
        rb.velocity = dir * currentSpeed;
    }


    public void IncreaseHitCounter()
    {
        if(hitCounter * extraSpeed <=  maxSpeed)
            hitCounter++;
    }
 


}

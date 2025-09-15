using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CollisionController : MonoBehaviour
{
      
   public BallMovement ballMovement;
    public ScoreScript ScoreScript;

    void BounceFromRocket(Collision2D collision)
    {
        Vector3 ballPosition = transform.position;
        Vector3 racketPossion = collision.gameObject.transform.position;

        float racketHeight = collision.collider.bounds.size.y;
        float x;

        if (collision.gameObject.name == "Player1")
        {
            x = 1;
        }else
        {
            x = -1;
        }


        float y = (ballPosition.y - racketPossion.y) / racketHeight;

        ballMovement.IncreaseHitCounter();
        ballMovement.MoveBall(new Vector2(x, y));
    }

    private void OnCollisionEnter2D(Collision2D collision)
    {
        if (collision.gameObject.name == "Player1" || collision.gameObject.name == "Player2")
        {
            BounceFromRocket(collision);
        }
        else if (collision.gameObject.name == "WallLeft")
        {
            ScoreScript.Player2Scored();
            StartCoroutine(ballMovement.StartBall(true));
        }
        else if (collision.gameObject.name == "WallRight")
        {
            ScoreScript.Player1Scored();
            StartCoroutine(ballMovement.StartBall(false));
        }

    }
}

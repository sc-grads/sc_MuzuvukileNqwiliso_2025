using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;
using UnityEngine.SceneManagement;

public class ScoreScript : MonoBehaviour
{
    private int PlayerScore1 = 0;
    private int PlayerScore2 = 0;

    public TMP_Text scoretextPlayer1;
    public TMP_Text scoretextPlayer2;

    public int goalTowin;


    void Update()
    {
        if (this.PlayerScore1 >= goalTowin)
        {
            Debug.Log("Player 1 Wins!");
            SceneManager.LoadScene("Game Over");
        }
        else if (PlayerScore2 >= goalTowin)
        {
            Debug.Log("Player 2 Wins!");
            SceneManager.LoadScene("Game Over");
        }
    }


    void FixedUpdate()
    {
        scoretextPlayer1.text = PlayerScore1.ToString();
        scoretextPlayer2.text = PlayerScore2.ToString();
    }


    public void Player1Scored()
    {
        PlayerScore1++;
    }


    public void Player2Scored()
    {
        PlayerScore2++;
    }
}

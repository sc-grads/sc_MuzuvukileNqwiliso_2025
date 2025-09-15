using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

public class GameManager : MonoBehaviour
{
    public bool hasGameStarted;
    public TMPro.TMP_Text scoreText;
    public TMPro.TMP_Text highScoreText;
    public int score;


    private void Awake()
    {
        highScoreText.text = "Best :" + GetHighScore().ToString();
    }

    public void StartGame()
    {
        hasGameStarted = true;
        FindObjectOfType<Road>().StartBuilding();
    }

    private void Update()
    {
        if(Input.GetKeyDown(KeyCode.Return))
        {
            StartGame();
        }

        if (Input.GetKeyDown(KeyCode.Escape))
        {

            ResetHighScore();
        }


    
     }

    public void  EndGame()
    {
        hasGameStarted = false;
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
    }

    public void IncreaseScore()
    {
        score++;
        scoreText.text = score.ToString();
        if (score > GetHighScore())
        {
            PlayerPrefs.SetInt("HighScore", score);
            highScoreText.text = "Best : " + score.ToString();
        }
    }

    public int GetHighScore()
    {
        return PlayerPrefs.GetInt("Best ", 0);
    }

    public void ResetHighScore()
    {
        score = 0;
    }

}

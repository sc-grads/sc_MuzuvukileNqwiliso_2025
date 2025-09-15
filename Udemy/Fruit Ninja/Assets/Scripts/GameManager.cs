using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class GameManager : MonoBehaviour {

    [Header("Score Elements")]
    public int score;
    public int highscore;
    public TextMeshProUGUI scoreText;
    public TextMeshProUGUI highscoreText;


    [Header("GameOver")]
    public GameObject gameOverPanel;
    public TextMeshProUGUI gameOverPanelScoreText;
    public TextMeshProUGUI gameOverPanelHighScoreText;

    private void Awake()
    {
        if (gameOverPanel == null)
        {
            Debug.LogWarning("gameOverPanel is not assigned in GameManager.Awake. Ensure it’s assigned before use.");
        }
        else
        {
            gameOverPanel.SetActive(false);
        }
        GetHighscore();
    }

    private void GetHighscore()
    {
        highscore = PlayerPrefs.GetInt("Highscore");
        if (highscoreText == null)
        {
            Debug.LogError("highscoreText is not assigned in GameManager. Please assign it in the Inspector.");
            return;
        }
        highscoreText.text = "Best: " + highscore;
    }


    public void IncreaseScore(int points){
        score += points;
        scoreText.text = score.ToString();

        if(score > highscore){
            PlayerPrefs.SetInt("Highscore", score);
            highscoreText.text = score.ToString();
        }

    }

    public void OnBombHit(){
        Time.timeScale = 0;

        gameOverPanelScoreText.text = "Score: " + score.ToString();
        gameOverPanelHighScoreText.text = "Best: " + highscore.ToString();
        gameOverPanel.SetActive(true);

        Debug.Log("Bomb hit");
    }

    public void RestartGame(){

        score = 0;
        scoreText.text = score.ToString();

        gameOverPanel.SetActive(false);

        foreach (GameObject g in GameObject.FindGameObjectsWithTag("Interactable")){
            Destroy(g);
        }

        Time.timeScale = 1;
    }

}

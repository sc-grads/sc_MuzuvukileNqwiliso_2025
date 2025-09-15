using UnityEngine;

public class Road : MonoBehaviour
{
    public GameObject roadPrefeb; // Prefab containing the cube and multiple child objects on top
    public Vector3 lastPosition;
    public float offset = 1.0f; // Adjusted to match block size, considering diagonal movement

    private int roadCount = 0;

    void Start()
    {
        // Initialize lastPosition to the position of the last existing block
        if (transform.childCount > 0)
        {
            lastPosition = transform.GetChild(transform.childCount - 1).position;
        }
        else
        {
            lastPosition = transform.position; // Default to this object's position if no children
        }
    }

    public void StartBuilding()
    {
        InvokeRepeating("CreateNewRoadPart", 1f, 0.2f);
    }

    public void CreateNewRoadPart()
    {
        Vector3 direction;

        if (Random.Range(0, 100) < 50)
        {
            direction = new Vector3(offset, 0, offset).normalized * offset; // Diagonal right
        }
        else
        {
            direction = new Vector3(-offset, 0, offset).normalized * offset; // Diagonal left
        }

        Vector3 spawnPos = lastPosition + direction;

        // Instantiate the full prefab (cube + children, with children hidden by default)
        GameObject obj = Instantiate(roadPrefeb, spawnPos, Quaternion.Euler(0, 45, 0));
        lastPosition = obj.transform.position; // Update lastPosition to the new block's position

        // Randomly decide whether to show an object on top (e.g., 50% chance)
        if (Random.Range(0, 100) < 50) // Adjust the percentage as needed
        {
            // Assuming there are multiple children, randomly select one to activate
            int childCount = obj.transform.childCount;
            if (childCount > 0)
            {
                int randomChildIndex = Random.Range(0, childCount);
                obj.transform.GetChild(randomChildIndex).gameObject.SetActive(true);
            }
        }

        roadCount++;
    }
}
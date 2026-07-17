using UnityEngine;
using UnityEngine.InputSystem;

public class CameraController : MonoBehaviour
{
    // Public variables to set in the Inspector
    public GameObject player;
    public float eyeHeight = 1.7f;         // Height above player pivot
    public float lookSpeed = 90.0f;        // Degrees per second for WASD look
    public float verticalClamp = 80.0f;    // Max look up/down angle
    public float horizontalClamp = 80.0f; // Max look left/right angle

    // Input system variables
    public InputAction lookAction;         // WASD look input

    private Vector2 lookInput; // Stores the current look input from the player 
    private float verticalRotation = 0f; // Current vertical rotation of the camera
    //private float horizontalRotation = 0f; // Current horizontal rotation of the camera

    void Start()
    {
        lookAction.Enable();
    }

    void LateUpdate()
    {
        lookInput = lookAction.ReadValue<Vector2>();

        // Position camera at player eye height
        transform.position = player.transform.position + Vector3.up * eyeHeight;

        // Horizontal look (A/D) - rotates camera only, NOT the player
        //horizontalRotation += lookInput.x * lookSpeed * Time.deltaTime;
        //horizontalRotation = Mathf.Clamp(horizontalRotation, -horizontalClamp, horizontalClamp);

        // Vertical look (W/S) - only rotates camera, not player
        verticalRotation -= lookInput.y * lookSpeed * Time.deltaTime;
        verticalRotation = Mathf.Clamp(verticalRotation, -verticalClamp, verticalClamp);

        // Apply rotation: match player's Y rotation + vertical tilt
        transform.rotation = Quaternion.Euler(verticalRotation, player.transform.eulerAngles.y, 0f);
        // transform.rotation = Quaternion.Euler(verticalRotation, player.transform.eulerAngles.y + horizontalRotation, 0f);
    }
}
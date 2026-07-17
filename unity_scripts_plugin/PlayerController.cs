using UnityEngine;
using UnityEngine.InputSystem;

public class PlayerController : MonoBehaviour
{
    // Public variables to set in the Inspector
   // public float speed = 6.0f; // not used, replaced with acceleration and deceleration
    public float turnSpeed = 120.0f; // Degrees per second for turning
    //public float drag = 3.0f;          // Higher = stops faster when no input

    // Input system variables
    public InputAction moveAction;      // Forward/back + turn (arrow keys)
    public InputAction stopAction;      // Stop button
    public float maxSpeed = 200.0f;
    public float acceleration = 10.0f;
    public float gravityMultiplier = 3.0f;
    public float turnRedirectSpeed = 50.0f; // Speed at which the player redirects to the camera's forward direction

   
    private Vector2 moveInput;
    private CharacterController cc;
    private Vector3 currentVelocity = Vector3.zero;
    private float verticalVelocity = 0f;
    public float deceleration = 3.0f;
    
    
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        
        moveAction.Enable();
        stopAction.Enable();

        cc = GetComponent<CharacterController>();

   
    }

    // Update is called once per frame
    void Update()
    {
        moveInput = moveAction.ReadValue<Vector2>();

        // Turn the player left/right (rotate around Y axis)
        transform.Rotate(Vector3.up, moveInput.x * turnSpeed * Time.deltaTime);

        // Stop button - zero velocity instantly
        if (stopAction.WasPressedThisFrame())
        {
            currentVelocity = Vector3.zero; 
        }

    // Acceleration/deceleration
        if (moveInput.y != 0)
        {
            currentVelocity += transform.forward * moveInput.y * acceleration * Time.deltaTime;
            if (currentVelocity.magnitude > maxSpeed)
            currentVelocity = currentVelocity.normalized * maxSpeed;
        }
        else
            currentVelocity = Vector3.MoveTowards(currentVelocity, Vector3.zero, deceleration * Time.deltaTime);

        // Redirect player velocity towards player forward direction
        currentVelocity = Vector3.RotateTowards(currentVelocity, transform.forward * currentVelocity.magnitude, turnRedirectSpeed * Mathf.Deg2Rad * Time.deltaTime, 0f);

    // Apply gravity
    // Apply gravity
        if (cc.isGrounded)
            verticalVelocity = 0f;
        else
            verticalVelocity += Physics.gravity.y* gravityMultiplier * Time.deltaTime;

        Vector3 motion = currentVelocity;
        motion.y = verticalVelocity;
        cc.Move(motion * Time.deltaTime);
    }
}


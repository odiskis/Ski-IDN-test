using UnityEngine;
using System.Runtime.InteropServices;

public class PositionReporter : MonoBehaviour
{
#if UNITY_WEBGL && !UNITY_EDITOR
    [DllImport("__Internal")]
    private static extern void SendPositionToParent(float x, float y, float z, string task, string status);
#endif

    // Called from the parent web page via:
    //   unityInstance.SendMessage("Player", "ReportPosition", "punkt-1|finished")
    public void ReportPosition(string taskAndStatus)
    {
        string[] parts = taskAndStatus.Split('|');
        string task = parts.Length > 0 ? parts[0] : "";
        string status = parts.Length > 1 ? parts[1] : "";

        Vector3 pos = transform.position;

#if UNITY_WEBGL && !UNITY_EDITOR
        SendPositionToParent(pos.x, pos.y, pos.z, task, status);
#else
        Debug.Log($"[PositionReporter] task={task} status={status} pos={pos}");
#endif
    }
}

mergeInto(LibraryManager.library, {
  SendPositionToParent: function (x, y, z, taskPtr, statusPtr) {
    var task = UTF8ToString(taskPtr);
    var status = UTF8ToString(statusPtr);
    if (window.parent) {
      window.parent.postMessage({
        type: 'terrain-task-result',
        task: task,
        status: status,
        unityX: x, unityY: y, unityZ: z
      }, '*');
    }
  }
});
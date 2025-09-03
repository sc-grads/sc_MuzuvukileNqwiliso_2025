namespace Generics.Task_Manager
{
    public class TaskProcessor
    {
        public void ProcessTask<T>(ITask<T> task, T taskData)
        {
            task.Execute(taskData);
        }
    }
}
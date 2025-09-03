namespace Generics.Task_Manager
{
    public interface ITask<T>
    {
        void Execute(T task);
    }
}
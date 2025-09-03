using System;

namespace Generics.Task_Manager
{
    public class ReportTask : ITask<int>
    {
        public void Execute(int reportId)
        {
            Console.WriteLine($"Generating report for ID: {reportId}");
        }
    }
}
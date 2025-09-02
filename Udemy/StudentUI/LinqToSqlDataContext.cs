using System.Data.SqlClient;

namespace StudentUI
{
    internal class LinqToSqlDataContext
    {
        private SqlConnection sqlConnection;
        private string connectionString;

        public LinqToSqlDataContext(SqlConnection sqlConnection)
        {
            this.sqlConnection = sqlConnection;
        }

        public LinqToSqlDataContext(string connectionString)
        {
            this.connectionString = connectionString;
        }

        public object Student { get; internal set; }
    }
}
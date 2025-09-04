using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Domain;

namespace Data
{
    public class Entities: DbContext
    {
        /// <summary>
        /// The bridge between the application and my Data
        /// This class is created a table 
        /// </summary>
        public DbSet<Flight> Flights => Set<Flight>();

        

        public Entities(DbContextOptions options): base(options) { }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<Flight>().HasKey(f => f.Id);
            modelBuilder.Entity<Flight>().OwnsMany(f => f.Bookings);
            base.OnModelCreating(modelBuilder);
        }
    }
}

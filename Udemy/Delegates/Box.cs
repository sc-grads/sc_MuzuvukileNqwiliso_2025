namespace Delegates
{
    internal class Box
    {
        private int v1;
        private int v2;

        public Box(int v1, int v2)
        {
            this.v1 = v1;
            this.v2 = v2;
        }

        public object X { get; internal set; }
    }
}
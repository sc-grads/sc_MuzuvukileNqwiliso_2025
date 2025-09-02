namespace Generics
{
    internal class Program
    {
        static void Main(string[] args)
        {
         Box<string> box = new Box<string>("Hello, Generics!");
            Console.WriteLine(box.GetContent());
            Console.WriteLine();
            box.UpdadteContent("Updated Content");
            Console.WriteLine(box.GetContent());

        }

        public void GenericMethod<T>(T parameter) // The T in parenthesis is a placeholder for any data type and is referencing the T in angle brackets next to the method name
                                                 // if the method name doesn't not gave the T next to it, you can not use the T in the method body
        {
            Console.WriteLine($"Parameter type: {typeof(T)}, Value: {parameter}");
        }



    }

    class Box<T>(T content)
    {
        public T Content = content;

        public void UpdadteContent(T newContent)
        {
            Content = newContent;
        }

        public T GetContent()
        {
            return Content;
        }

    }

    class Box2<T1, T2>(T1 content1, T2 content2)
    {
        public T1 Content1 = content1;
        public T2 Content2 = content2;
        public void UpdateContents(T1 newContent1, T2 newContent2)
        {
            Content1 = newContent1;
            Content2 = newContent2;
        }
        public (T1, T2) GetContents()
        {
            return (Content1, Content2);
        }
    }

    class Box3<T>
    {
        // In order for you to use a generic type, you must make sure it have a reference type constraint where T 

        public T Content;
    }
}

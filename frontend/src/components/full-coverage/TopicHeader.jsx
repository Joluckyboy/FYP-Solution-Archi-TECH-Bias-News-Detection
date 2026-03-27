const TopicHeader = ({ title }) => {
    return (
        <div className="mb-8">
            <h1 className="text-4xl md:text-5xl font-bold text-slate-900 leading-tight">
                {title}
            </h1>
        </div>
    );
};

export default TopicHeader;

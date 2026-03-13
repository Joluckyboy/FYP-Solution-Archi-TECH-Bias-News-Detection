const TopicHeader = ({ title }) => {
    return (
        <div className="mb-8">
            <h1 className="text-3xl md:text-4xl font-bold text-slate-900 leading-tight">
                {title}
            </h1>
        </div>
    );
};

export default TopicHeader;

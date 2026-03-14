export default function Footer() {
    return (
        <footer className="w-full bg-gray-900 text-white py-6">
            <div className="container mx-auto px-6 md:px-12">
                <div>
                    <h2 className="text-xl font-bold">CheckMate</h2>
                    <p className="text-sm text-gray-400 mt-2">
                        There is no news that is completely unbiased. We provide a range of perspectives on today's news to help you decide! ☻
                    </p>
                </div>

                {/* Bottom Section */}
                <div className="border-t border-gray-700 mt-6 pt-4 text-center text-sm text-gray-500">
                    &copy; {new Date().getFullYear()} CheckMate. All rights reserved.
                </div>
            </div>
        </footer>
    );
}
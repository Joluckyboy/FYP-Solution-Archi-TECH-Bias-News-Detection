import { Facebook, Twitter, Instagram, Mail } from "lucide-react";

export default function Footer() {
    return (
        <footer className="w-full bg-gray-900 text-white py-6">
            <div className="container mx-auto px-6 md:px-12">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Brand Info */}
                    <div>
                        <h2 className="text-xl font-bold">CheckMate</h2>
                        <p className="text-sm text-gray-400 mt-2">
                            Your trusted ally against misinformation. Verify before you believe.
                        </p>
                    </div>

                    {/* Links */}
                    <div>
                        <h3 className="text-lg font-semibold">Quick Links</h3>
                        <ul className="mt-2 space-y-2 text-gray-400">
                            <li><a href="/about" className="hover:text-white">About Us</a></li>
                            <li><a href="/faq" className="hover:text-white">FAQ</a></li>
                            <li><a href="/resources" className="hover:text-white">Resources</a></li>
                            <li><a href="/contact" className="hover:text-white">Contact</a></li>
                        </ul>
                    </div>

                    {/* Socials & Contact */}
                    <div>
                        <h3 className="text-lg font-semibold">Stay Connected</h3>
                        <div className="flex gap-4 mt-2">
                            <a href="#" className="text-gray-400 hover:text-white"><Facebook size={20} /></a>
                            <a href="#" className="text-gray-400 hover:text-white"><Twitter size={20} /></a>
                            <a href="#" className="text-gray-400 hover:text-white"><Instagram size={20} /></a>
                            <a href="mailto:info@checkmate.com" className="text-gray-400 hover:text-white"><Mail size={20} /></a>
                        </div>
                    </div>
                </div>

                {/* Bottom Section */}
                <div className="border-t border-gray-700 mt-6 pt-4 text-center text-sm text-gray-500">
                    &copy; {new Date().getFullYear()} CheckMate. All rights reserved.
                </div>
            </div>
        </footer>
    );
}
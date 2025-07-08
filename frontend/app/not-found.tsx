import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-white">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">404 - Page Not Found</h1>
        <p className="text-gray-600 mb-8">The page you&apos;re looking for doesn&apos;t exist.</p>
        <Link
          href="/"
          className="bg-ai-primary text-white px-6 py-3 rounded-lg font-medium hover:bg-ai-primary/90 transition-colors"
        >
          Go Home
        </Link>
      </div>
    </div>
  );
}
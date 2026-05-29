export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Autoscience</h1>
        <p className="text-xl text-gray-600 mb-8">
          Background Scientific Cognition System
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <a href="/projects" className="block p-6 bg-white rounded-lg shadow hover:shadow-lg transition">
            <h2 className="text-xl font-semibold mb-2">Projects</h2>
            <p className="text-gray-600">Manage your research projects</p>
          </a>
          
          <a href="/projects" className="block p-6 bg-white rounded-lg shadow hover:shadow-lg transition">
            <h2 className="text-xl font-semibold mb-2">Ideas</h2>
            <p className="text-gray-600">Track and score research ideas</p>
          </a>
          
          <a href="/projects" className="block p-6 bg-white rounded-lg shadow hover:shadow-lg transition">
            <h2 className="text-xl font-semibold mb-2">Literature</h2>
            <p className="text-gray-600">Browse papers and clusters</p>
          </a>
          
          <a href="/projects" className="block p-6 bg-white rounded-lg shadow hover:shadow-lg transition">
            <h2 className="text-xl font-semibold mb-2">Skills</h2>
            <p className="text-gray-600">View learned research skills</p>
          </a>
          
          <a href="/projects" className="block p-6 bg-white rounded-lg shadow hover:shadow-lg transition">
            <h2 className="text-xl font-semibold mb-2">Reports</h2>
            <p className="text-gray-600">Read research reports</p>
          </a>
          
          <a href="/projects" className="block p-6 bg-white rounded-lg shadow hover:shadow-lg transition">
            <h2 className="text-xl font-semibold mb-2">Settings</h2>
            <p className="text-gray-600">Configure project settings</p>
          </a>
        </div>
      </div>
    </main>
  );
}

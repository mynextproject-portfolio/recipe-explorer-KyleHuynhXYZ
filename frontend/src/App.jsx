import { useState, useEffect } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { useDebounce } from './hooks/useDebounce';
import RecipeCard from './components/RecipeCard';
import RecipeModal from './components/RecipeModal';

export default function App() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 500);
  
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [selectedRecipe, setSelectedRecipe] = useState(null);

  useEffect(() => {
    async function fetchRecipes() {
      setLoading(true);
      setError(null);
      try {
        const url = debouncedQuery 
          ? `http://localhost:8000/api/recipes?search=${encodeURIComponent(debouncedQuery)}`
          : 'http://localhost:8000/api/recipes';
          
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch recipes');
        
        const data = await response.json();
        setRecipes(data.recipes || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchRecipes();
  }, [debouncedQuery]);

  return (
    <div className="min-h-screen font-sans selection:bg-black selection:text-white">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <h1 className="text-2xl font-black tracking-tight">RECIPE // EXPLORER</h1>
            
            {/* Search Bar */}
            <div className="relative max-w-md w-full">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Craving a steakhouse ribeye or quick street food?"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-3 bg-gray-100 border-transparent rounded-full focus:bg-white focus:border-black focus:ring-2 focus:ring-black outline-none transition-all"
              />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {error && (
          <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-8 font-medium border border-red-200">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 text-gray-400">
            <Loader2 className="w-10 h-10 animate-spin mb-4 text-black" />
            <p className="font-medium tracking-wide">CURATING RECIPES...</p>
          </div>
        ) : recipes.length === 0 ? (
          <div className="text-center py-20">
            <h3 className="text-2xl font-bold mb-2">No recipes found</h3>
            <p className="text-gray-500">Try adjusting your search terms.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {recipes.map((recipe) => (
              <RecipeCard 
                key={recipe.id} 
                recipe={recipe} 
                onClick={setSelectedRecipe} 
              />
            ))}
          </div>
        )}
      </main>

      {/* Detail Modal */}
      <RecipeModal 
        recipe={selectedRecipe} 
        onClose={() => setSelectedRecipe(null)} 
      />
    </div>
  );
}
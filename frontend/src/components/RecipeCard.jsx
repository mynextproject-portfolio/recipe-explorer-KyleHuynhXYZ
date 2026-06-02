import { ChefHat, ExternalLink, Clock } from 'lucide-react';

export default function RecipeCard({ recipe, onClick }) {
  const isExternal = recipe.source === 'external';

  return (
    <div 
      onClick={() => onClick(recipe)}
      className="bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-lg transition-all cursor-pointer group"
    >
      <div className="h-48 bg-gray-100 flex items-center justify-center relative overflow-hidden">
        {/* Placeholder Image - Minimalist style */}
        <ChefHat className="w-16 h-16 text-gray-300 group-hover:scale-110 transition-transform duration-300" />
        
        {/* Source Badge */}
        <span className={`absolute top-4 right-4 text-xs font-bold px-3 py-1 rounded-full ${
          isExternal ? 'bg-blue-100 text-blue-700' : 'bg-black text-white'
        }`}>
          {isExternal ? 'Web' : 'Original'}
        </span>
      </div>
      
      <div className="p-5">
        <h3 className="font-bold text-xl mb-2 line-clamp-1">{recipe.title}</h3>
        <p className="text-gray-600 text-sm mb-4 line-clamp-2">
          {recipe.description || 'A delicious culinary experience awaits.'}
        </p>
        
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span className="flex items-center gap-1">
            <Clock className="w-4 h-4" /> {recipe.cuisine || 'Global'}
          </span>
          {isExternal && <ExternalLink className="w-4 h-4" />}
        </div>
      </div>
    </div>
  );
}
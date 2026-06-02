import { X, CheckCircle2 } from 'lucide-react';

export default function RecipeModal({ recipe, onClose }) {
  if (!recipe) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-center items-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto shadow-2xl relative animate-in fade-in zoom-in-95 duration-200">
        
        <button 
          onClick={onClose}
          className="absolute top-6 right-6 p-2 bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="p-8 md:p-10">
          <div className="mb-8">
            <span className="text-sm font-bold tracking-widest uppercase text-gray-500">{recipe.cuisine}</span>
            <h2 className="text-3xl md:text-4xl font-black mt-2 mb-4">{recipe.title}</h2>
            <p className="text-lg text-gray-600">{recipe.description}</p>
          </div>

          <div className="grid md:grid-cols-3 gap-10">
            <div className="md:col-span-1">
              <h3 className="text-xl font-bold mb-4 border-b pb-2">Ingredients</h3>
              <ul className="space-y-3">
                {recipe.ingredients?.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-gray-700">
                    <CheckCircle2 className="w-5 h-5 text-black shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="md:col-span-2">
              <h3 className="text-xl font-bold mb-4 border-b pb-2">Instructions</h3>
              <ol className="space-y-6 list-decimal list-inside">
                {recipe.instructions?.map((step, idx) => (
                  <li key={idx} className="text-gray-700 leading-relaxed pl-2">
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
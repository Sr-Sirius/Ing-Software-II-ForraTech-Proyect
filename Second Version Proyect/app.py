from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET","POST"])
def index():

    forrajes = []

    if request.method == "POST":

        altura = int(request.form["altura"])
        clima = request.form["clima"]

        if altura >= 2000 and clima == "frio":

            forrajes = [

                {
                "nombre":"Alfalfa",
                "img":"alfalfa.jpg",
                "desc":"La alfalfa es una leguminosa forrajera de alto valor nutricional. Contiene gran cantidad de proteína, vitaminas y minerales que ayudan al desarrollo de los animales. Es utilizada en la alimentación de bovinos, ovinos y caprinos y además mejora la fertilidad del suelo al fijar nitrógeno."
                },

                {
                "nombre":"Trébol blanco",
                "img":"trebol_bla.jpg",
                "desc":"El trébol blanco es una leguminosa que se adapta bien a climas fríos y templados. Aporta proteína a la dieta animal y mejora la fertilidad del suelo. Es común en sistemas ganaderos donde se busca mejorar la calidad del forraje."
                },

                {
                "nombre":"Avena forrajera",
                "img":"avena.jpg",
                "desc":"La avena forrajera es un cultivo muy utilizado en la alimentación animal por su rápida producción de biomasa. Puede usarse para pastoreo, corte o ensilaje y aporta energía en la dieta del ganado."
                },

                {
                "nombre":"Cebada forrajera",
                "img":"cebada.jpg",
                "desc":"La cebada forrajera se adapta bien a climas fríos y zonas de altura. Es utilizada como alimento para ganado por su buen valor energético y puede aprovecharse en pastoreo o para ensilaje."
                },

                {
                "nombre":"Vicia",
                "img":"vicia.jpg",
                "desc":"La vicia es una leguminosa anual utilizada como forraje por su alto contenido de proteína. Se cultiva frecuentemente junto con cereales para mejorar la calidad nutricional del alimento animal."
                }

            ]

        elif altura >= 1000 and altura < 2000 and clima == "templado":

            forrajes = [

                {
                "nombre":"Leucaena",
                "img":"leucaena.jpg",
                "desc":"La leucaena es un árbol forrajero utilizado en sistemas silvopastoriles. Sus hojas contienen alto contenido de proteína y son consumidas por bovinos, ovinos y caprinos. También ayuda a mejorar la fertilidad del suelo."
                },

                {
                "nombre":"Centrosema",
                "img":"centrosema.jpg",
                "desc":"El centrosema es una leguminosa rastrera utilizada como forraje y cobertura vegetal. Mejora el valor nutritivo de la alimentación animal y ayuda a conservar la fertilidad del suelo."
                },

                {
                "nombre":"Estilosantes",
                "img":"estilosantes.jpg",
                "desc":"Los estilosantes son leguminosas tropicales que se utilizan para mejorar la calidad de las pasturas. Son resistentes y aportan proteína a la dieta animal."
                },

                {
                "nombre":"Kudzu tropical",
                "img":"kudzu.jpg",
                "desc":"El kudzu tropical es una planta leguminosa trepadora que produce abundante biomasa. Se utiliza como forraje y también como cobertura vegetal para proteger el suelo."
                },

                {
                "nombre":"Maíz forrajero",
                "img":"maiz.jpg",
                "desc":"El maíz forrajero es uno de los cultivos más utilizados para producir ensilaje. Proporciona energía a los animales y permite almacenar alimento para épocas de escasez."
                }

            ]

        elif altura < 1000 and clima == "calido":

            forrajes = [

                {
                "nombre":"Cratylia",
                "img":"cratylia.jpg",
                "desc":"La cratylia es un arbusto forrajero resistente a sequías y climas tropicales. Se utiliza como suplemento proteico para mejorar la dieta del ganado."
                },

                {
                "nombre":"Matarratón",
                "img":"matarraton.jpg",
                "desc":"El matarratón es un árbol forrajero muy utilizado en sistemas agroforestales. Sus hojas se emplean como suplemento en la alimentación animal."
                },

                {
                "nombre":"Nacedero",
                "img":"nacedero.jpg",
                "desc":"El nacedero es un arbusto forrajero muy nutritivo utilizado principalmente en la alimentación de cabras y ovejas. Tiene alto contenido de proteína."
                },

                {
                "nombre":"Leucaena",
                "img":"leucaena.jpg",
                "desc":"La leucaena también se adapta bien a climas cálidos y es utilizada como suplemento proteico en sistemas ganaderos tropicales."
                },

                {
                "nombre":"Sorgo forrajero",
                "img":"sorgo.jpg",
                "desc":"El sorgo forrajero es un cultivo resistente al calor y a la sequía. Se utiliza para producir alimento para el ganado y también para ensilaje."
                }

            ]

        else:

            forrajes = [{
                "nombre":"Sin resultados",
                "img":"error.jpg",
                "desc":"No se encontraron especies forrajeras recomendadas para las condiciones ingresadas."
            }]

    return render_template("index.html", forrajes=forrajes)

if __name__ == "__main__":
    app.run(debug=True)
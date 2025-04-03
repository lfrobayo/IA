productos = ["arroz","manzanas","aceite"]
arroz={"precio":10, "cantidad":10}
manzana={"precio":10, "cantidad":10}
aceite={"precio":10, "cantidad":10}
bandera = True
while bandera:
    print("1. Agregar producto")
    print("2. Buscar producto")
    print("3. Mostrar todos los productos")
    print("4. Salir")
    opcion = int(input("Ingrese una opcion: "))
    if opcion == 1:
        producto = input("Ingrese el nombre del producto: ")
        if producto in productos:
            print("el objeto ya esta")
        else:
            productos.append(producto)
            producto={"precio":0,"cantidad":0}
            temp=int(input("Ingrese el precio "))
            producto["precio"]=temp
            temp=int(input("Ingrese la cantidad "))
            producto["cantidad"]=temp
            print(producto)
            print("Producto agregado")
    elif opcion == 2:
        var=input("Ingrese el nombre del producto a buscar: ").lower()
        
        if var in productos:
            print("el producto "+var+" esta en la tienda y cuenta con el siguiente inventario")
            
        else:
            print("el objeto no esta en la tienda")
    elif opcion == 3:
        for x in productos:
            print(x)
    elif opcion == 4:
        print("adios")
        bandera = False
    else:
        print("Opcion no valida")
print("Fin del programa")
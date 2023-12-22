from notion_client import Client
notion = Client(auth="secret_ScBU2Kyc4uFD7co3kECqS5yCkkmkulTgQ7SSuS9YS0M")
databaseID = "00f6fa861276497580fbf6ef48bc53e9"

parishList = ["Assumption, Broadview Heights","Blessed Trinity, Akron","Blessed Trinity, Cleveland","Cathedral of Saint John the Evangelist, Cleveland","Communion of Saints, Cleveland Heights","Divine Word, Kirtland","Gesu, University Heights","Guardian Angels, Copley","Holy Angels, Bainbridge","Holy Family, Parma","Holy Family, Stow","Holy Martyrs, Medina","Holy Name, Cleveland","Holy Redeemer, Cleveland","Holy Rosary, Cleveland","Holy Spirit, Avon Lake","Holy Spirit, Garfield Heights","Holy Trinity, Avon","Immaculate Conception, Akron","Immaculate Conception, Cleveland","Immaculate Conception, Madison","Immaculate Conception, Willoughby","Immaculate Heart of Mary, Cleveland","Immaculate Heart of Mary, Cuyahoga Falls","Mary Queen of Apostles, Brook Park","Mary Queen of Peace, Cleveland","Mother of Sorrows, Peninsula","Nativity of the Blessed Virgin Mary, Lorain","Nativity of the Blessed Virgin Mary, South Amherst","Nativity of the Lord Jesus, Akron","Our Lady Help of Christians, Litchfield","Our Lady Help of Christians, Lodi","Our Lady Help of Christians, Nova","Our Lady Help of Christian, Seville","Our Lady of Angels, Cleveland","Our Lady of Grace, Hinckley","Our Lady of Guadalupe, Macedonia","Our Lady of Hope, Bedford","Our Lady of Lourdes, Cleveland","Our Lady of Mount Carmel, Cleveland","Our Lady of Mount Carmel, Wickliffe","Our Lady of Peace, Cleveland","Our Lady of the Lake, Euclid","Our Lady of Victory, Tallmadge","Our Lady Queen of Peace, Grafton","Prince of Peace, Norton","Resurrection of Our Lord, Solon","Sacred Heart, Oberlin","Sacred Heart Chapel, Lorain","Sacred Heart of Jesus, South Euclid","Sacred Heart of Jesus, Wadsworth","Sagrada Familia, Cleveland","St. Adalbert, Berea","St. Adalbert, Cleveland","St. Agnes - Our Lady of Fatima, Cleveland","St. Agnes, Elyria","St. Agnes, Orrville","St. Albert the Great, North Royalton","St. Aloysius - St. Agatha, Cleveland","St. Ambrose, Brunswick","St. Andrew Kim, Cleveland","St. Andrew the Apostle, Norton","St. Angela Merici, Fairview Park","St. Anne, Rittman","St. Anselm, Chesterland","St. Anthony of Padua, Akron","St. Anthony of Padua, Fairport Harbor","St. Anthony of Padua, Lorain","St. Anthony of Padua, Parma","St. Augustine, Barberton","St. Augustine, Cleveland","St. Barbara, Cleveland","St. Barnabas, Northfield","St. Bartholomew, Middleburg Heights","St. Basil The Great, Brecksville","St. Bede the Venerable, Mentor","St. Bernadette, Westlake","St. Bernard, Akron","St. Boniface, Cleveland","St. Brendan, North Olmsted","St. Bridget of Kildare, Parma","St. Casimir, Cleveland","St. Casimir, Euclid","St. Charles Borromeo, Parma","St. Christopher, Rocky River","St. Clare, Lyndhurst","St. Clarence, North Olmsted","St. Clement, Lakewood","St. Colette, Brunswick","St. Colman, Cleveland","St. Columbkille, Parma","St. Cyprian, Perry","St. Dominic, Shaker Heights","St. Edward, Ashland","St. Edward, Parkman","St. Emeric, Cleveland","St. Elizabeth Ann Seton, Columbia Station","St. Elizabeth of Hungry, Cleveland","St. Eugene, Cuyahoga Falls","St. Francis de Sales, Akron","St. Francis de Sales, Parma","St. Francis Xavier, Medina","St. Francis Xavier Cabrini, Lorain","St. Francis of Assissi, Gates Mills","St. Gabriel, Concord","St. Helen, Newbury","St. Hilary, Fairlawn","St. Ignatius of Antioch, Cleveland","St. James, Lakewood","St. Jerome, Cleveland","St. Joan of Arc, Chagrin Falls","St. John Cantius, Cleveland","St. John Nepomucene, Cleveland","St. John Bosco, Parma Heights","St. John of the Cross, Euclid","St. John the Baptist, Akron","St. John Neumann, Strongsville","St. John Vianney, Mentor","St. Joseph, Amherst","St. Joseph, Avon Lake","St. Joseph, Strongsville","St. Joseph, Cuyahoga Falls","St. Jude, Elryia","St. Julie Billiart, North Ridgeville","St. Justin Martyr, Eastlake","St. Ladislas, Westlake","St. Leo the Great, Cleveland","St. Lucy Mission, Middlefield","St. Luke, Lakewood","St. Malachi, Cleveland","St. Matthew, Akron","St. Mark, Cleveland","St. Martin of Tours, Maple Heights","St. Martin of Tours, Valley City","St. Mary, Akron","St. Mary, Bedford","St. Mary, Berea","St. Mary, Chardon","St. Mary, Cleveland (Collonwood)","St. Mary, Elyria","St. Mary, Hudson","St. Mary, Lorain","St. Mary, Painesville","St. Mary Magdalene, Willowick","St. Mary of the Assumption, Mentor","St. Mary of the Falls, Olmsted Falls","St. Mary of the Immaculate Conception, Avon","St. Mary of the Immaculate Conception, Wooster","St. Matthias, Parma","St. Mel, Cleveland","St. Michael, Independence","St. Michael the Archangel, Cleveland","St. Monica, Garfield Heights","St. Noel, Willoughby","St. Paschal Baylon, Highland Heights","St. Patrick, Cleveland (Bridge)","St. Patrick, Cleveland (Rocky River)","St. Patrick, Thompson","St. Patrick, Wellington","St. Paul, Akron","St. Paul, Cleveland","St. Peter, Cleveland","St. Peter, Lorain","St. Peter, Loudonville","St. Peter, North Ridgeville","St. Raphael, Bay Village","St. Richard, North Olmsted","St. Rita, Solon","St. Rocco, Cleveland","St. Sebastian, Akron","St. Stanislaus, Cleveland","St. Stephen, Cleveland","St. Stephen, West Salem","St. Therese, Garfield Heights","St. Theresa of Avila, Sheffield ","St. Thomas, Sheffield Lake","St. Thomas More, Brooklyn","St. Victor, Richfield","St. Vincent de Paul, Akron","St. Vincent de Paul, Cleveland","St. Vincent de Paul, Elyria","St. Vitus, Cleveland","St. Wendelin, Cleveland","Ss. Cosmas and Damian, Twinsburg","Ss. Peter and Paul, Doylestown","Ss. Peter and Paul, Garfield Heights","Ss. Robert and William, Euclid","Transfiguration, Lakewood","Queen of Heaven, Uniontown","Visitation of Mary, Akron"]

def createParish(parishName):
    notion.pages.create(
        **{
            "parent": {
                "database_id": databaseID
            },
            "properties": {
                "Name": {
                    "title":[ 
                        {
                            "text": {
                                "content": parishName
                                }
                        }
                    ]
                }
                #"Column 2 goes here"
            }
        }
    )

def findPageID(parishName):
    response = notion.databases.query(
        **{"database_id": databaseID,
           "filter": {
               "property": "Name",
               "title": {"equals": parishName}
            }
        }
    )
    resultList = [i["id"] for i in response['results']]
    print(resultList)    

for parish in parishList:
    findPageID(parish)  #Find the ID of the parish
    #print(findPageID(parish))
#    createParish(parish)   #Create a parish in the database

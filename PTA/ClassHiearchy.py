
from email.mime import base
from typing import Dict, Generator, List, Set, Tuple

from .PointToSet import PointToSet
from .Pointers import VarPtr
from .Objects import ClassObject, FakeObject

# Here MRO mean an order in which methods are resolved, a tuple consists of class objects
MRO = Tuple[ClassObject, ...]
SubclassInfo = Tuple[ClassObject, int]
class ClassHiearchy:
    mros: Dict[ClassObject, Set[MRO]]
    subClasses: Dict[ClassObject, Set[SubclassInfo]]
    pointToSet: PointToSet
    def __init__(self, pointToSet):
        self.mros = {}
        self.pointToSet = pointToSet
        self.subClasses = {}

    def addClass(self, classObj: ClassObject) -> Set[MRO]:
        assert(isinstance(classObj, ClassObject))
        if(classObj in self.mros):
            return
        self.mros[classObj] = set()
        self.subClasses[classObj] = set()
        bases = classObj.getBases()
        
        for i in range(len(bases)):
            for baseObj in self.pointToSet.get(bases[i]):
                self._getSubClasses(baseObj).add((classObj, i))

        add = self.addBaseMRO(classObj, -1, {})

        return add

        
    def addClassBase(self, classObj: ClassObject, index: int, baseObj: ClassObject) -> Set[MRO]:
        assert(isinstance(classObj, ClassObject))

        self._getSubClasses(baseObj).add((classObj, index))
        return self.addBaseMRO(classObj, index, self._getMROs(baseObj))

    def addBaseMRO(self, classObj: ClassObject, index: int, mroList: Set[MRO]) -> Set[MRO]:
        assert(isinstance(classObj, ClassObject))
        bases = classObj.getBases()
        # yield mros
        def select(start: int) -> Generator[List[MRO], None, None]:
            if(start == len(bases)):
                yield []
                
            elif(start == index):
                for mro in mroList:
                    for tail in select(start + 1):
                        tail.insert(0, mro)
                        yield tail
            else:
                for obj in self.pointToSet.get(bases[start]):
                    for mro in self._getMROs(obj):
                        for tail in select(start + 1):
                            tail.insert(0, mro)
                            yield tail
                # TODO: ugly!
                # objs = self.pointToSet.get(bases[start])
                # if(len(objs) == 0):
                #     yield [(None,)]
                # else:
                #     for obj in objs:
                #         for mro in self.mros[obj]:
                #             for tail in select(start + 1):
                #                 tail.insert(0, mro)
                #                 yield tail

        add = set()
        for mros in select(0):
            order = [mro[0] for mro in mros]
            mros.append(order)
            res = classObj, *self._merge(mros)
            
            if(res is not None and res not in self.mros[classObj]):
                assert(res[0] == classObj)
                add.add(res)
                self.mros[classObj].add(res)
                
        if(len(add) == 0):
            return set()

        allAdd = add.copy()
        for subclass, index in self.subClasses[classObj]:
            allAdd |= self.addBaseMRO(subclass, index, add)
        return allAdd

    # return None if it is illegal
    def _merge(self, mros: List) -> MRO:
        for i in range(len(mros)):
            mros[i] = list(mros[i])
        res = []
        mros = [mro for mro in mros if len(mro) != 0]
        while(len(mros) != 0):
            for mro in mros:
                candidate = mro[0]
                
                for another in mros:
                    if(candidate in  another[1:]):
                        break
                else:
                    res.append(candidate)
                    for another in mros:
                        if(another[0] == candidate):
                            del another[0]
                    mros = [mro for mro in mros if len(mro) != 0]
                    break
            else:
                # illegal mro
                return None
            
        return *res,

    def _getSubClasses(self, classObj: ClassObject) -> Set[ClassObject]:
        if(isinstance(classObj, FakeObject) and classObj not in self.subClasses):
            self.subClasses[classObj] = set()
        return self.subClasses[classObj]

    def _getMROs(self, classObj: ClassObject) -> Set[MRO]:
        if(isinstance(classObj, FakeObject) and classObj not in self.mros):
            self.mros[classObj] = {(classObj, )}
        return self.mros[classObj]

    def getMROs(self, classObj: ClassObject) -> Set[MRO]:
        if(classObj in self.mros):
            return self.mros[classObj]
        else:
            return set()

    def dump(self, fp):
        
        for classObj, mros in self.mros.items():
            head = f"{classObj}: "
            w = len(head)
            
            for mro in mros:
                print(f"{head:<{w}}{', '.join([str(parent) for parent in mro])}", file=fp)
                head = ""
            
            

        print("", file=fp)
        
        for classObj, subInfos in self.subClasses.items():
            head = f"{classObj} -> "
            w = len(head)
            
            for subInfo in subInfos:
                print(f"{head:<{w}}{subInfo[0]} : {subInfo[1]}", file=fp)
                head = ""




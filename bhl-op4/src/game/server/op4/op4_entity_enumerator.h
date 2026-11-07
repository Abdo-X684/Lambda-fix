/* OP4 dlls/util.h:597-735, verbatim. Standalone so it can be unit-tested on the host. */
#ifndef OP4_BHL_ENTITY_ENUMERATOR_H
#define OP4_BHL_ENTITY_ENUMERATOR_H


/* ---------------------------------------------------------------------------
 * OP4-MERGE (dlls/util.h:597-735, verbatim, @5368be7f8eba):
 * CEntityIterator / CEntityEnumerator and UTIL_FindEntitiesByClassname.
 * OP4's CTF sources use these range-based wrappers; BHL exposes only the
 * singular UTIL_FindEntityByClassname(), which is exactly what the functors
 * below call. No BHL interface is changed.
 * -------------------------------------------------------------------------*/
template <typename T>
struct FindByClassnameFunctor
{
	static T* Find(T* pStartEntity, const char* pszClassname)
	{
		return static_cast<T*>(UTIL_FindEntityByClassname(pStartEntity, pszClassname));
	}
};

template <typename T>
struct FindByTargetnameFunctor
{
	static T* Find(T* pStartEntity, const char* pszName)
	{
		return static_cast<T*>(UTIL_FindEntityByTargetname(pStartEntity, pszName));
	}
};

template <typename T, typename FINDER>
class CEntityIterator
{
public:
	CEntityIterator()
		: m_pszName(""), m_pEntity(nullptr)
	{
	}

	CEntityIterator(const CEntityIterator&) = default;

	CEntityIterator(const char* const pszName, T* pEntity)
		: m_pszName(pszName), m_pEntity(pEntity)
	{
	}

	CEntityIterator& operator=(const CEntityIterator&) = default;

	const T* operator*() const { return m_pEntity; }

	T* operator*() { return m_pEntity; }

	T* operator->() { return m_pEntity; }

	void operator++()
	{
		m_pEntity = static_cast<T*>(FINDER::Find(m_pEntity, m_pszName));
	}

	void operator++(int)
	{
		++*this;
	}

	bool operator==(const CEntityIterator& other) const
	{
		return m_pEntity == other.m_pEntity;
	}

	bool operator!=(const CEntityIterator& other) const
	{
		return !(*this == other);
	}

private:
	const char* const m_pszName;
	T* m_pEntity;
};

template <typename T, typename FINDER>
class CEntityEnumerator
{
public:
	using Functor = FINDER;
	using iterator = CEntityIterator<T, Functor>;

	CEntityEnumerator(const char* pszClassName)
		: m_pszName(pszClassName)
	{
	}

	iterator begin()
	{
		return {m_pszName, static_cast<T*>(Functor::Find(nullptr, m_pszName))};
	}

	iterator end()
	{
		return {m_pszName, nullptr};
	}

private:
	const char* const m_pszName;
};

template <typename T, typename FINDER>
class CEntityEnumeratorWithStart
{
public:
	using Functor = FINDER;
	using iterator = CEntityIterator<T, Functor>;

	CEntityEnumeratorWithStart(const char* pszClassName, T* pStartEntity)
		: m_pszName(pszClassName), m_pStartEntity(pStartEntity)
	{
	}

	iterator begin()
	{
		return {m_pszName, static_cast<T*>(Functor::Find(m_pStartEntity, m_pszName))};
	}

	iterator end()
	{
		return {m_pszName, nullptr};
	}

private:
	const char* const m_pszName;
	T* m_pStartEntity = nullptr;
};

template <typename T = CBaseEntity>
inline CEntityEnumerator<T, FindByClassnameFunctor<T>> UTIL_FindEntitiesByClassname(const char* pszClassName)
{
	return {pszClassName};
}

template <typename T = CBaseEntity>
inline CEntityEnumeratorWithStart<T, FindByClassnameFunctor<T>> UTIL_FindEntitiesByClassname(const char* pszClassName, T* pStartEntity)
{
	return {pszClassName, pStartEntity};
}

template <typename T = CBaseEntity>
inline CEntityEnumerator<T, FindByTargetnameFunctor<T>> UTIL_FindEntitiesByTargetname(const char* pszName)
{
	return {pszName};
}

template <typename T = CBaseEntity>
inline CEntityEnumeratorWithStart<T, FindByTargetnameFunctor<T>> UTIL_FindEntitiesByTargetname(const char* pszName, T* pStartEntity)
{
	return {pszName, pStartEntity};
}

#endif /* OP4_BHL_ENTITY_ENUMERATOR_H */

import tenseal as ts

def encrypted_euclidean_squared(enc_vec_bytes, stored_vec_bytes, context):
    """
    Compute the encrypted squared Euclidean distance between two CKKS vectors.

    Args:
        enc_vec_bytes (bytes): Serialized CKKS vector (query/user).
        stored_vec_bytes (bytes): Serialized CKKS vector (from DB).
        context (ts.Context): TenSEAL context (public).

    Returns:
        ts.CKKSVector: Encrypted squared Euclidean distance.
    """
    enc_vec = ts.lazy_ckks_vector_from(enc_vec_bytes)
    enc_vec.link_context(context)
    stored_vec = ts.lazy_ckks_vector_from(stored_vec_bytes)
    stored_vec.link_context(context)
    diff = enc_vec - stored_vec
    return diff.dot(diff)
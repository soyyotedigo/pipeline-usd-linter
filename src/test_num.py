import numpy as np


def quat_to_matrix(q):
    """
    q en formato (w, x, y, z)
    devuelve matriz 4x4
    """
    w, x, y, z = q

    xx = x * x
    yy = y * y
    zz = z * z
    xy = x * y
    xz = x * z
    yz = y * z
    wx = w * x
    wy = w * y
    wz = w * z

    m = np.eye(4, dtype=float)

    m[0, 0] = 1 - 2 * (yy + zz)
    m[0, 1] = 2 * (xy - wz)
    m[0, 2] = 2 * (xz + wy)

    m[1, 0] = 2 * (xy + wz)
    m[1, 1] = 1 - 2 * (xx + zz)
    m[1, 2] = 2 * (yz - wx)

    m[2, 0] = 2 * (xz - wy)
    m[2, 1] = 2 * (yz + wx)
    m[2, 2] = 1 - 2 * (xx + yy)

    return m


def trs_to_matrix(translation, rotation_quat, scale):
    """
    translation: (tx, ty, tz)
    rotation_quat: (w, x, y, z)
    scale: (sx, sy, sz)
    """
    t = np.eye(4, dtype=float)
    t[3, 0:3] = translation

    r = quat_to_matrix(rotation_quat)

    s = np.eye(4, dtype=float)
    s[0, 0] = scale[0]
    s[1, 1] = scale[1]
    s[2, 2] = scale[2]

    # USD usa convención fila/vector bastante distinta según contexto.
    # Para chequeo interno consistente, mantené la misma convención siempre.
    return s @ r @ t


def is_identity_matrix(m, tol=1e-4):
    return np.allclose(m, np.eye(4), atol=tol)


def rotation_angle_from_matrix(m):
    """
    ángulo de rotación en grados de una matriz 4x4
    """
    r = m[:3, :3]
    trace = np.trace(r)
    value = (trace - 1.0) / 2.0
    value = np.clip(value, -1.0, 1.0)
    angle_rad = np.arccos(value)
    return np.degrees(angle_rad)


def translation_length_from_matrix(m):
    t = m[3, 0:3]
    return np.linalg.norm(t)


# ejemplo
rest = np.eye(4)

current = trs_to_matrix(
    translation=(-1.4418598e-15, 66.85012, 0.82930076),
    rotation_quat=(0.7065522, 0.02799997, -0.02799997, 0.7065522),  # identidad
    scale=(1.0, 1.0, 1.0)
)

print(current)

delta = np.linalg.inv(rest) @ current

print("Delta es identidad:", is_identity_matrix(delta))
print("Ángulo delta:", rotation_angle_from_matrix(delta))
print("Traslación delta:", translation_length_from_matrix(delta))


def quat_is_identity(q, tol=1e-4):
    w, x, y, z = q
    return (
        abs(w - 1.0) < tol and
        abs(x) < tol and
        abs(y) < tol and
        abs(z) < tol
    )

print(quat_is_identity((0.7065522, 0.02799997, -0.02799997, 0.7065522)))

def translation_is_zero(t, tol=1e-4):
    return all(abs(v) < tol for v in t)

print(translation_is_zero((-1.4418598e-15, 66.85012, 0.82930076)))

def scale_is_one(s, tol=1e-4):
    return (
        abs(s[0] - 1.0) < tol and
        abs(s[1] - 1.0) < tol and
        abs(s[2] - 1.0) < tol
    )

print(scale_is_one((1.0, 1.0, 1.0)))


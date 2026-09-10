"""モジュラモノリス + DDD のカーネル (共通モジュール)。

公開 API はここでは再エクスポートしない。利用側は ddd4py.common.application.transactional の
ように、責務のあるモジュールを直接指して import する (どの層に属する型なのかを import 文に残す)。
"""

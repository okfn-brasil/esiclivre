from esiclivre import browser


class Pedido(object):
    def __init__(self, raw_data):
        pass


class ListaDePedidos(object):

    """Docstring for ListaDePedidos. """

    _full_data_tag_name = 'ctl00_MainContent_grid_pedido'

    def __init__(self, navegador):
        """TODO: to be defined1. """

        self._full_data = navegador.find_element_by_id(
            self._full_data_tag_name).find_element_by_id('tbody')

        self._pedido_keys = [
            el.text for el in main_element.find_elements_by_tag_name('th')
        ]
        del(main_element.find_element_by_id('tr'))

        self._pedidos = [Pedido(data) for data in
                         self._full_data.find_elements_by_tag_name('tr')]

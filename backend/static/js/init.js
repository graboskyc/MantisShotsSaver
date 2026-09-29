function init() {
    return {
        foo: "",
        

        async loadList() {
            console.log('Loading List');
            this.foo= await (await fetch('/api/hello')).json();
            console.log(this.foo);
        },

        delay(ms) {
            return new Promise(resolve => setTimeout(resolve, ms))
        },
          


    }
}